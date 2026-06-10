/**
 * useRecommend — 유일한 API 통신 지점 (FE-A/FE-B 공용).
 * 컴포넌트에서 직접 fetch 금지 (AGENT.md §7-4). 모든 /recommend 호출은 이 훅을 경유한다.
 *
 * VITE_USE_MOCK=true 면 mocks/recommend.ts 를, 아니면 실서버 POST /recommend 를 호출한다.
 * 로딩 중에는 S-02 단계 진행(step)을 프론트 타이밍으로 점등(방식 A)하고,
 * 재검색 시나리오에선 화면 전환 없이 refining 플래그만 켠다.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import type { RecommendRequest, RecommendResponse } from '../types/api';
import { isErrorTrigger, mockRecommend } from '../mocks/recommend';

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';
const API_BASE = import.meta.env.VITE_API_BASE ?? '';

/** 통신 단계 (App viewState 와는 별개의 통신 상태) */
export type Phase = 'idle' | 'loading' | 'done' | 'error';

/** S-02 파이프라인 단계 수 (입력 분석 → 약점 분석 → 멘토 검색 → 적합도 평가) */
export const STEP_COUNT = 4;

const STEP_INTERVAL = 450; // ms, 단계당 점등 간격
const REFINE_DELAY = 900; // ms, 재검색 연출 추가 지연
const TIMEOUT_HINT = 8000; // ms, 이 시간 넘으면 timeout 힌트

export interface SubmitInput {
  project_text: string;
  tech_stack?: string[];
  stage?: string;
  /** 확인 질문 응답 시에만 값 (동일 session 유지) */
  clarify_answer?: string | null;
}

export interface UseRecommendResult {
  phase: Phase;
  data: RecommendResponse | null;
  error: string | null;
  /** 현재 진행 중인 파이프라인 단계 index (0..STEP_COUNT-1) */
  step: number;
  /** 재검색 중 여부 (S-02 안내 한 줄) */
  refining: boolean;
  /** 응답 지연으로 timeout 힌트를 보여야 하는지 */
  timedOut: boolean;
  /** 추천 요청. 성공 시 응답을, 실패 시 throw. App이 status로 화면을 분기한다. */
  submit: (input: SubmitInput) => Promise<RecommendResponse>;
  /** 처음으로 — 세션 폐기 후 초기화 */
  reset: () => void;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function callServer(req: RecommendRequest): Promise<RecommendResponse> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`서버 오류 (${res.status})`);
  return (await res.json()) as RecommendResponse;
}

export function useRecommend(): UseRecommendResult {
  const [phase, setPhase] = useState<Phase>('idle');
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const [refining, setRefining] = useState(false);
  const [timedOut, setTimedOut] = useState(false);

  const sessionIdRef = useRef<string>(crypto.randomUUID());
  const mountedRef = useRef(true);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearTimers();
    };
  }, [clearTimers]);

  const reset = useCallback(() => {
    clearTimers();
    sessionIdRef.current = crypto.randomUUID();
    setPhase('idle');
    setData(null);
    setError(null);
    setStep(0);
    setRefining(false);
    setTimedOut(false);
  }, [clearTimers]);

  const submit = useCallback(
    async (input: SubmitInput): Promise<RecommendResponse> => {
      clearTimers();
      setPhase('loading');
      setData(null);
      setError(null);
      setStep(0);
      setRefining(false);
      setTimedOut(false);

      // 단계 점등 타이머 (프론트 연출, 방식 A)
      for (let i = 1; i < STEP_COUNT; i += 1) {
        timersRef.current.push(
          setTimeout(() => {
            if (mountedRef.current) setStep(i);
          }, STEP_INTERVAL * i),
        );
      }
      // timeout 힌트 타이머
      timersRef.current.push(
        setTimeout(() => {
          if (mountedRef.current) setTimedOut(true);
        }, TIMEOUT_HINT),
      );

      const req: RecommendRequest = {
        session_id: sessionIdRef.current,
        project_text: input.project_text,
        tech_stack: input.tech_stack,
        stage: input.stage,
        clarify_answer: input.clarify_answer ?? null,
      };

      try {
        let response: RecommendResponse;

        if (USE_MOCK) {
          await sleep(STEP_INTERVAL * STEP_COUNT); // 단계가 한 바퀴 도는 시간
          if (isErrorTrigger(req)) throw new Error('강제 에러 트리거');
          response = mockRecommend(req);

          // 재검색 연출: limited 또는 refined 추천이면 refining 한 박자
          const willRefine =
            response.status === 'limited' ||
            (response.status === 'recommended' && response.refined);
          if (willRefine) {
            if (mountedRef.current) setRefining(true);
            await sleep(REFINE_DELAY);
          }
        } else {
          // 실서버는 응답이 매우 빠르므로(~10ms) 그냥 두면 분석 진행 화면(S-02)이
          // 사용자 눈에 보이지 않는다. 단계가 한 바퀴 도는 시간만큼 최소 로딩을
          // 보장해, 진행 중임을 명시적으로 보여준다(서버 호출과 동시 진행).
          const [serverResponse] = await Promise.all([
            callServer(req),
            sleep(STEP_INTERVAL * STEP_COUNT),
          ]);
          response = serverResponse;

          // 재검색 연출: limited 또는 refined 추천이면 refining 한 박자(mock 과 동일)
          const willRefine =
            response.status === 'limited' ||
            (response.status === 'recommended' && response.refined);
          if (willRefine) {
            if (mountedRef.current) setRefining(true);
            await sleep(REFINE_DELAY);
          }
        }

        clearTimers();
        if (mountedRef.current) {
          setStep(STEP_COUNT - 1);
          setRefining(false);
          setTimedOut(false);
          setData(response);
          setPhase('done');
        }
        return response;
      } catch (e) {
        clearTimers();
        const message =
          e instanceof Error ? e.message : '알 수 없는 오류가 발생했어요.';
        if (mountedRef.current) {
          setError(message);
          setPhase('error');
        }
        throw e;
      }
    },
    [clearTimers],
  );

  return {
    phase,
    data,
    error,
    step,
    refining,
    timedOut,
    submit,
    reset,
  };
}
