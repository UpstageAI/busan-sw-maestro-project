import { useState } from "react";
import { AlertTriangle, Server } from "lucide-react";
import { analyzeText } from "./api/client";
import { AnalyzeForm } from "./components/AnalyzeForm";
import { AnalysisHistory } from "./components/AnalysisHistory";
import { ReportView } from "./components/ReportView";
import { Sidebar } from "./components/Sidebar";
import { WorkflowStatus } from "./components/WorkflowStatus";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  AnalyzeState,
  AppPage,
  WorkflowProgressEvent,
  WorkflowStep,
} from "./types";

const initialRequest: AnalyzeRequest = {
  text: "",
  senderRole: "",
  receiverRole: "",
  communicationType: "",
};

export default function App() {
  const [request, setRequest] = useState<AnalyzeRequest>(initialRequest);
  const [report, setReport] = useState<AnalyzeResponse | null>(null);
  const [historyReport, setHistoryReport] = useState<AnalyzeResponse | null>(null);
  const [state, setState] = useState<AnalyzeState>("idle");
  const [error, setError] = useState("");
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [activePage, setActivePage] = useState<AppPage>("analyze");
  const [completedSteps, setCompletedSteps] = useState<WorkflowStep[]>([]);
  const [progressLabel, setProgressLabel] = useState("");

  const handleAnalyze = async () => {
    if (
      !request.text.trim() ||
      !request.senderRole ||
      !request.receiverRole ||
      !request.communicationType
    ) {
      setError("분석할 텍스트, 발화자·수신자 직군, 소통 유형을 모두 입력해주세요.");
      setState("error");
      return;
    }

    setState("loading");
    setError("");
    setReport(null);
    setCompletedSteps([]);
    setProgressLabel("분석 작업을 시작하는 중입니다.");

    try {
      const response = await analyzeText(request, handleProgress);
      setReport(response);
      setState("success");
      setProgressLabel("최종 보고서 생성 완료");
      setHistoryRefreshKey((current) => current + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석 중 오류가 발생했습니다.");
      setState("error");
    }
  };

  const handleProgress = (event: WorkflowProgressEvent) => {
    setProgressLabel(event.label);
    setCompletedSteps((current) =>
      current.includes(event.step) ? current : [...current, event.step],
    );
  };

  const handleHistorySelect = (selectedReport: AnalyzeResponse) => {
    setHistoryReport(selectedReport);
    setError("");
  };

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-ink">
      <div className="flex">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />

        <main className="min-w-0 flex-1 px-8 py-7">
          <header className="mb-7 flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-black text-brand">ContextBridge MVP</p>
              <h1 className="mt-2 text-3xl font-black tracking-tight text-ink">
                {activePage === "analyze"
                  ? "협업 텍스트 오해 가능 용어 분석"
                  : "분석 이력"}
              </h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                {activePage === "analyze"
                  ? "협업 텍스트를 입력하고 오해 가능 용어와 합의 필요 항목을 분석합니다."
                  : "완료된 분석 목록을 조회하고 이전 보고서를 다시 확인합니다."}
              </p>
            </div>
          </header>

          {error ? (
            <div className="mb-5 flex items-center gap-2 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-danger">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          ) : null}

          {activePage === "analyze" ? (
            <>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-2 text-xs font-black text-muted">
                <Server className="h-4 w-4 text-brand" />
                VITE_API_BASE_URL 미설정 시 mock mode로 동작
              </div>

              <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.7fr)]">
                <AnalyzeForm
                  value={request}
                  isLoading={state === "loading"}
                  onChange={setRequest}
                  onSubmit={handleAnalyze}
                />
                <WorkflowStatus
                  state={state}
                  route={report?.route}
                  completedSteps={completedSteps}
                  progressLabel={progressLabel}
                />
              </div>

              <div className="mt-6">
                <ReportView report={report} />
              </div>
            </>
          ) : (
            <div className="grid gap-6">
              <AnalysisHistory
                refreshKey={historyRefreshKey}
                onSelect={handleHistorySelect}
                onError={setError}
              />
              <ReportView
                report={historyReport}
                emptyMessage="분석 이력 카드를 선택하면 이 영역에 과거 보고서가 표시됩니다."
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
