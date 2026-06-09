import clsx from "clsx";
import { ClipboardList, History, MessageSquareText } from "lucide-react";
import type { AppPage } from "../types";

const navItems: Array<{ id: AppPage; label: string; description: string; icon: typeof History }> = [
  {
    id: "analyze",
    label: "분석하기",
    description: "협업 텍스트 분석",
    icon: MessageSquareText,
  },
  {
    id: "history",
    label: "분석 이력",
    description: "완료 보고서 조회",
    icon: History,
  },
];

export function Sidebar({
  activePage,
  onNavigate,
}: {
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}) {
  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col bg-slate-950 px-5 py-7 text-white">
      <div>
        <p className="text-2xl font-black tracking-tight">ContextBridge</p>
        <p className="mt-2 text-xs font-medium text-slate-400">협업 문맥 오해 탐지 Agent</p>
      </div>

      <nav className="mt-12 grid gap-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.id === activePage;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={clsx(
                "flex items-center gap-3 rounded-lg px-3 py-3 text-left transition",
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-900 hover:text-white",
              )}
            >
              <span
                className={clsx(
                  "grid h-9 w-9 shrink-0 place-items-center rounded-lg",
                  isActive ? "bg-brand text-white" : "bg-slate-900 text-slate-400",
                )}
              >
                <Icon className="h-4 w-4" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-black">{item.label}</span>
                <span className="mt-0.5 block text-xs font-medium text-slate-500">
                  {item.description}
                </span>
              </span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg bg-slate-900 p-4 text-xs leading-6 text-slate-300">
        <p className="mb-2 flex items-center gap-2 font-bold text-white">
          <ClipboardList className="h-4 w-4" />
          MVP 범위
        </p>
        <p>분석 이력 목록/상세 조회</p>
        <p>텍스트 입력 기반 분석</p>
        <p>보고서형 결과 출력</p>
      </div>
    </aside>
  );
}
