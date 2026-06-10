/**
 * api.ts — POST /recommend 요청·응답 타입 (단일 진실 소스)
 *
 * 프론트는 이 엔드포인트 하나만 호출하고, 응답 `status` 하나로 모든 화면 분기를 결정한다.
 * 화면마다 인라인 타입을 새로 만들지 않는다 (AGENT.md §7-5).
 *
 * 백엔드 GraphState(backend/app/graph/state.py)와의 개념 매핑:
 *   clarification_question → question
 *   gap_analysis          → gaps
 *   final_recommendations  → mentors
 *   message               → notice (limited)
 * HTTP 응답 스키마는 백엔드와 1주차 초 확정(AGENT.md §5). 바뀌면 이 파일만 갱신한다.
 */

/** 추천 요청 본문 */
export interface RecommendRequest {
  /** uuid. 신규 또는 확인 질문 후 동일 세션 */
  session_id: string;
  /** 자유 텍스트 (필수) */
  project_text: string;
  /** 선택 — 구조화 입력 */
  tech_stack?: string[];
  /** 선택 — 진행 단계 */
  stage?: string;
  /** 확인 질문 응답 시에만 값 */
  clarify_answer?: string | null;
}

/** 멘토 프로필 — data/mentors.json 합성 데이터 형태와 동일 */
export interface Mentor {
  name: string;
  domain: string[];
  keywords: string[];
  /** 적합도 0~100 */
  score: number;
  /** 추천 이유 (백엔드 생성, 그대로 표시 — 프론트 가공 금지) */
  reason: string;
  can_help: string[];
  less_relevant_for: string[];
  profile_summary: string;
}

/** 입력이 부족해 확인 질문이 필요한 경우 → CLARIFY (S-03) */
export interface NeedClarificationResponse {
  status: 'need_clarification';
  /** 백엔드 question 그대로 표시 */
  question: string;
  /** 있으면 칩/버튼, 없으면 자유 입력만 */
  options?: string[];
}

/** 정상 추천 → RESULT (S-04) */
export interface RecommendedResponse {
  status: 'recommended';
  /** 분석된 약점 키워드 (그대로 표시) */
  gaps: string[];
  /** 재검색이 일어났는지 */
  refined: boolean;
  mentors: Mentor[];
}

/** 재검색 후에도 근거 약함 → RESULT (S-04) + 제한 배너 */
export interface LimitedResponse {
  status: 'limited';
  gaps: string[];
  mentors: Mentor[];
  /** 제한적 추천 안내 (그대로 표시) */
  notice: string;
}

/** /recommend 응답 — status 3종 (discriminated union) */
export type RecommendResponse =
  | NeedClarificationResponse
  | RecommendedResponse
  | LimitedResponse;

/** 응답에서 gaps를 안전하게 꺼내기 위한 헬퍼 타입 가드 */
export function hasMentors(
  res: RecommendResponse,
): res is RecommendedResponse | LimitedResponse {
  return res.status === 'recommended' || res.status === 'limited';
}
