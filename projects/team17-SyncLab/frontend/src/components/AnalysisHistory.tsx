import { Clock3, History, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getAnalysis, getAnalyses } from "../api/client";
import type { AnalysisHistoryItem, AnalyzeResponse } from "../types";

type AnalysisHistoryProps = {
  refreshKey: number;
  onSelect: (report: AnalyzeResponse) => void;
  onError: (message: string) => void;
};

export function AnalysisHistory({ refreshKey, onSelect, onError }: AnalysisHistoryProps) {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    try {
      setItems(await getAnalyses());
    } catch (error) {
      onError(error instanceof Error ? error.message : "분석 이력을 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [onError]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory, refreshKey]);

  const handleSelect = async (id: string) => {
    setLoadingId(id);
    try {
      onSelect(await getAnalysis(id));
    } catch (error) {
      onError(error instanceof Error ? error.message : "분석 상세를 불러오지 못했습니다.");
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <section className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-black text-ink">
            <History className="h-5 w-5 text-brand" />
            최근 분석 이력
          </h2>
          <p className="mt-1 text-sm text-muted">완료된 분석을 선택해 보고서를 다시 확인합니다.</p>
        </div>
        <button
          type="button"
          onClick={() => void loadHistory()}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-xs font-black text-muted transition hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-50"
          title="분석 이력 새로고침"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          새로고침
        </button>
      </div>

      {isLoading ? (
        <div className="mt-5 flex items-center gap-2 rounded-lg bg-slate-50 p-4 text-sm font-bold text-muted">
          <Loader2 className="h-4 w-4 animate-spin text-brand" />
          분석 이력을 불러오는 중입니다.
        </div>
      ) : items.length === 0 ? (
        <div className="mt-5 rounded-lg border border-dashed border-line p-5 text-center text-sm font-bold text-muted">
          아직 완료된 분석 이력이 없습니다.
        </div>
      ) : (
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => void handleSelect(item.id)}
              disabled={loadingId !== null}
              className="min-w-0 rounded-lg border border-line bg-white p-4 text-left transition hover:border-brand hover:bg-blue-50 disabled:cursor-wait disabled:opacity-60"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-black text-muted">
                  {item.senderRole || "직군 미상"}
                </span>
                <span className="flex items-center gap-1 text-xs font-bold text-muted">
                  {loadingId === item.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Clock3 className="h-3.5 w-3.5" />
                  )}
                  {formatDate(item.createdAt)}
                </span>
              </div>
              <p className="mt-3 line-clamp-2 text-sm font-black leading-6 text-ink">{item.summary}</p>
              <p className="mt-2 line-clamp-2 text-xs font-medium leading-5 text-muted">
                {item.keyRequest}
              </p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
