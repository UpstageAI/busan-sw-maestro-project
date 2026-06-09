import { delay, http, HttpResponse } from "msw";
import { findMockCase } from "../api/client";
import { testCases } from "../data/testCases";
import type {
  AnalysisHistoryItem,
  AnalyzeApiRequest,
  TestCase,
  WorkflowEvent,
  WorkflowStep,
} from "../types";

const workflowSteps: Array<{ step: WorkflowStep; label: string }> = [
  { step: "context_intake", label: "문맥 분석 완료" },
  { step: "word_extractor", label: "핵심 단어 추출 완료" },
  { step: "role_worker", label: "직군별 의미 해석 완료" },
  { step: "risk_term", label: "위험 용어 선별 완료" },
  { step: "synthesis", label: "위험도 종합 분석 완료" },
  { step: "report", label: "최종 보고서 생성 완료" },
];

const pendingJobs = new Map<string, TestCase>();
const completedReports = new Map(testCases.map((testCase) => [testCase.id, testCase.response]));
const mockHistory: AnalysisHistoryItem[] = testCases.slice(0, 5).map((testCase, index) => ({
  id: testCase.id,
  summary: testCase.response.summary,
  keyRequest: testCase.response.keyRequest,
  senderRole: testCase.request.senderRole || "직군 미상",
  createdAt: new Date(Date.now() - index * 60 * 60 * 1000).toISOString(),
}));

export const handlers = [
  http.post("*/api/analyze", async ({ request }) => {
    const body = (await request.json()) as Partial<AnalyzeApiRequest>;

    if (!body.text?.trim() || !body.communicationType?.trim() || (body.participants?.length ?? 0) < 2) {
      return HttpResponse.json(
        {
          detail: "분석할 텍스트와 필수 소통 정보를 입력해주세요.",
        },
        { status: 400 },
      );
    }

    const mockCase = findMockCase({
      text: body.text,
      senderRole: body.participants?.[0]?.role ?? "",
      receiverRole: body.participants?.[1]?.role ?? "",
      communicationType: body.communicationType,
    });
    const jobId = crypto.randomUUID();
    pendingJobs.set(jobId, mockCase);

    await delay(250);
    return HttpResponse.json({ job_id: jobId }, { status: 202 });
  }),
  http.get("*/api/analyze/:jobId/stream", ({ params }) => {
    const jobId = String(params.jobId);
    const mockCase = pendingJobs.get(jobId);

    if (!mockCase) {
      return HttpResponse.json({ detail: "존재하지 않는 job_id입니다." }, { status: 404 });
    }

    const stream = createMockSseStream(jobId, mockCase);

    return new HttpResponse(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  }),
  http.get("*/api/analyses", async () => {
    await delay(250);
    return HttpResponse.json(mockHistory);
  }),
  http.get("*/api/analyses/:id", async ({ params }) => {
    const report = completedReports.get(String(params.id));

    await delay(250);

    if (!report) {
      return HttpResponse.json({ detail: "존재하지 않는 분석 ID입니다." }, { status: 404 });
    }

    return HttpResponse.json(report);
  }),
];

function createMockSseStream(jobId: string, mockCase: TestCase) {
  const encoder = new TextEncoder();

  return new ReadableStream({
    async start(controller) {
      for (const progress of workflowSteps) {
        await delay(350);
        enqueueEvent(controller, {
          type: "progress",
          step: progress.step,
          label: progress.label,
        });
      }

      await delay(300);
      enqueueEvent(controller, { type: "done", result: mockCase.response });
      controller.close();

      pendingJobs.delete(jobId);
      completedReports.set(jobId, mockCase.response);
      mockHistory.unshift({
        id: jobId,
        summary: mockCase.response.summary,
        keyRequest: mockCase.response.keyRequest,
        senderRole: mockCase.request.senderRole,
        createdAt: new Date().toISOString(),
      });
    },
  });

  function enqueueEvent(controller: ReadableStreamDefaultController, event: WorkflowEvent) {
    controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
  }
}
