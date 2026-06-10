import clsx from "clsx";
import { Check, CircleDashed, GitBranch } from "lucide-react";
import type { AnalyzeState, RouteType, WorkflowStep } from "../types";
import { routeDescription, routeLabel } from "../utils";

const steps: Array<{
  id: WorkflowStep;
  label: string;
  description: string;
}> = [
  {
    id: "context_intake",
    label: "문맥 분석",
    description: "소통 상황과 문맥 충분성을 판단합니다.",
  },
  {
    id: "word_extractor",
    label: "핵심 단어 추출",
    description: "모호할 수 있는 핵심 용어를 찾습니다.",
  },
  {
    id: "role_worker",
    label: "직군별 의미 해석",
    description: "참여 직군 관점의 의미를 병렬 분석합니다.",
  },
  {
    id: "risk_term",
    label: "위험 용어 선별",
    description: "오해 가능성이 높은 용어를 선별합니다.",
  },
  {
    id: "synthesis",
    label: "위험도 종합 분석",
    description: "해석 차이와 위험도를 종합합니다.",
  },
  {
    id: "report",
    label: "최종 보고서 생성",
    description: "합의 질문과 체크리스트를 생성합니다.",
  },
];

export function WorkflowStatus({
  state,
  route,
  completedSteps,
  progressLabel,
}: {
  state: AnalyzeState;
  route?: RouteType;
  completedSteps: WorkflowStep[];
  progressLabel: string;
}) {
  const activeIndex =
    state === "loading"
      ? steps.findIndex((step) => !completedSteps.includes(step.id))
      : state === "success"
        ? steps.length
        : 0;

  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-black text-ink">Agent Workflow</h2>
          <p className="mt-1 text-sm text-muted">
            {state === "loading" && progressLabel ? progressLabel : routeDescription(route)}
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-black text-bridge">
          <GitBranch className="h-3.5 w-3.5" />
          {state === "loading" ? "실시간 분석 중" : routeLabel(route)}
        </span>
      </div>

      <div className="mt-5 grid gap-3">
        {steps.map((step, index) => {
          const isDone = state === "success" || completedSteps.includes(step.id);
          const isActive = state === "loading" && index === activeIndex;

          return (
            <div
              key={step.id}
              className={clsx(
                "grid grid-cols-[2rem_1fr_auto] items-center gap-3 rounded-lg border p-3",
                isActive && "border-brand bg-blue-50",
                isDone && !isActive && "border-green-100 bg-green-50",
                !isDone && !isActive && "border-line bg-slate-50",
              )}
            >
              <span
                className={clsx(
                  "grid h-8 w-8 place-items-center rounded-full text-xs font-black",
                  isDone && "bg-success text-white",
                  isActive && !isDone && "bg-brand text-white",
                  !isDone && !isActive && "bg-slate-300",
                )}
              >
                {isDone ? (
                  <Check className="h-4 w-4" />
                ) : isActive ? (
                  <CircleDashed className="h-4 w-4 animate-spin" />
                ) : (
                  index + 1
                )}
              </span>
              <div>
                <p className="text-sm font-black text-ink">{step.label}</p>
                <p className="text-xs text-muted">{step.description}</p>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-muted ring-1 ring-line">
                {isDone ? "완료" : isActive ? "진행 중" : "대기"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
