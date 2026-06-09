import { testCases } from "../data/testCases";
import type {
  AnalysisHistoryItem,
  AnalyzeApiRequest,
  AnalyzeRequest,
  AnalyzeResponse,
  JobResponse,
  TestCase,
  WorkflowEvent,
  WorkflowProgressEvent,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

export function findMockCase(request: AnalyzeRequest): TestCase {
  const normalized = request.text.trim();

  if (!request.senderRole || !request.receiverRole) {
    return testCases.find((item) => item.route === "need_more_context") ?? testCases[0];
  }

  return (
    testCases.find((item) => normalized && item.request.text.includes(normalized.slice(0, 18))) ??
    testCases.find((item) => item.request.communicationType === request.communicationType) ??
    testCases[0]
  );
}

export async function analyzeText(
  request: AnalyzeRequest,
  onProgress: (event: WorkflowProgressEvent) => void,
): Promise<AnalyzeResponse> {
  const startResponse = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(toApiRequest(request)),
  });
  const startBody = (await startResponse.json()) as JobResponse | { detail?: string; message?: string };

  if (!startResponse.ok) {
    throw new Error(getErrorMessage(startBody, "분석 요청에 실패했습니다."));
  }

  return receiveAnalysisStream((startBody as JobResponse).job_id, onProgress);
}

export async function getAnalyses(): Promise<AnalysisHistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/analyses`);
  const body = (await response.json()) as AnalysisHistoryItem[] | { detail?: string; message?: string };

  if (!response.ok) {
    throw new Error(getErrorMessage(body, "분석 이력을 불러오지 못했습니다."));
  }

  return body as AnalysisHistoryItem[];
}

export async function getAnalysis(id: string): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyses/${encodeURIComponent(id)}`);
  const body = (await response.json()) as AnalyzeResponse | { detail?: string; message?: string };

  if (!response.ok) {
    throw new Error(getErrorMessage(body, "분석 상세를 불러오지 못했습니다."));
  }

  return body as AnalyzeResponse;
}

function getErrorMessage(body: unknown, fallback: string) {
  if (typeof body === "object" && body !== null) {
    if ("detail" in body && typeof body.detail === "string") {
      return body.detail;
    }

    if ("message" in body && typeof body.message === "string") {
      return body.message;
    }
  }

  return fallback;
}

function toApiRequest(request: AnalyzeRequest): AnalyzeApiRequest {
  return {
    text: request.text,
    participants: [
      { name: "발화자", role: request.senderRole },
      { name: "수신자", role: request.receiverRole },
    ],
    communicationType: request.communicationType,
  };
}

async function receiveAnalysisStream(
  jobId: string,
  onProgress: (event: WorkflowProgressEvent) => void,
): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze/${encodeURIComponent(jobId)}/stream`, {
    headers: { Accept: "text/event-stream" },
  });

  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    throw new Error(getErrorMessage(body, "분석 진행 스트림 연결에 실패했습니다."));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const event = parseSseBlock(block);

      if (!event) {
        continue;
      }

      if (event.type === "progress") {
        onProgress(event);
      } else if (event.type === "done") {
        return event.result;
      } else {
        throw new Error(event.message);
      }
    }

    if (done) {
      break;
    }
  }

  throw new Error("분석 스트림이 결과 없이 종료되었습니다.");
}

function parseSseBlock(block: string): WorkflowEvent | null {
  const data = block
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .join("\n");

  return data ? (JSON.parse(data) as WorkflowEvent) : null;
}
