/**
 * recommend.ts — /recommend mock 응답 (백엔드 완성 전 병렬 개발용)
 *
 * 입력 텍스트 / clarify_answer 키워드로 데모 시나리오 3종 + 빈/에러를 라우팅한다.
 * useRecommend() 가 VITE_USE_MOCK=true 일 때만 사용한다 (AGENT.md §6).
 *
 * 데모 시나리오:
 *   1) "배포·서빙·MLOps"  → recommended (멘토 O)
 *   2) "구조·아키텍처·기획" → need_clarification → (답변 후) recommended
 *   3) "WebRTC·실시간·영상" → limited (refined:true, notice)
 *   그 외: 의미 없는 입력 → empty(mentors []) / "강제에러" 포함 → ERROR(useRecommend가 throw)
 */
import type {
  Mentor,
  RecommendRequest,
  RecommendResponse,
} from '../types/api';

/** 합성 멘토 풀 (실제 멘토 개인정보 아님 — 기획서 MVP 합성 데이터) */
export const MENTORS: Record<string, Mentor> = {
  seo: {
    name: '서지훈',
    domain: ['MLOps', 'Infra'],
    keywords: ['model serving', 'docker', 'kubernetes', 'deployment'],
    score: 92,
    reason:
      '모델 서빙과 배포 경험 부족이라는 현재 약점과 직접 연결됩니다. 서빙 파이프라인 구성과 무중단 배포 경험이 많아 곧 다가올 배포 단계에 바로 도움을 줄 수 있습니다.',
    can_help: ['모델 서빙 구조 설계', '컨테이너 기반 배포', '운영 환경 구성'],
    less_relevant_for: ['초기 UX 리서치', '브랜딩 전략'],
    profile_summary: '모델 서빙과 백엔드 인프라 설계를 주로 다뤄온 MLOps 멘토',
  },
  jang: {
    name: '장민서',
    domain: ['Backend', 'Deploy'],
    keywords: ['fastapi', 'ci/cd', 'observability', 'docker-compose'],
    score: 85,
    reason:
      'FastAPI 백엔드를 운영 단계로 끌어올린 경험이 있어, 배포 자동화와 모니터링 관점에서 약점을 보완해 줄 수 있습니다.',
    can_help: ['CI/CD 파이프라인', '배포 자동화', '운영 모니터링'],
    less_relevant_for: ['데이터 라벨링', '디자인 시스템'],
    profile_summary: '백엔드 운영과 배포 자동화에 강한 멘토',
  },
  yoon: {
    name: '윤서연',
    domain: ['Architecture', 'Backend'],
    keywords: ['system design', 'scalability', 'api design', 'review'],
    score: 88,
    reason:
      '시스템 구조의 적절성에 대한 확신이 부족한 상황과 맞닿아 있습니다. 다양한 서비스의 아키텍처 리뷰 경험을 바탕으로 구조적 위험을 짚어줄 수 있습니다.',
    can_help: ['아키텍처 리뷰', '확장성 설계', 'API 경계 설계'],
    less_relevant_for: ['모바일 네이티브', '하드웨어 펌웨어'],
    profile_summary: '시스템 설계와 구조 리뷰를 전문으로 하는 멘토',
  },
  han: {
    name: '한도윤',
    domain: ['Security', 'Backend'],
    keywords: ['auth', 'threat modeling', 'secure design'],
    score: 79,
    reason:
      '구조 검토 시 보안 관점의 빈틈을 함께 점검할 수 있습니다. 인증·권한 설계와 위협 모델링 경험이 있습니다.',
    can_help: ['인증·인가 설계', '위협 모델링', '보안 리뷰'],
    less_relevant_for: ['그로스 마케팅', '데이터 시각화'],
    profile_summary: '백엔드 보안과 안전한 설계를 다루는 멘토',
  },
  oh: {
    name: '오현우',
    domain: ['Realtime', 'Backend'],
    keywords: ['websocket', 'media server', 'low latency'],
    score: 64,
    reason:
      '실시간 시스템과 미디어 서버 경험이 있어 관련성은 있으나, WebRTC 영상 처리에 정확히 특화된 멘토는 아니라 근거가 다소 제한적입니다.',
    can_help: ['실시간 메시징 구조', '저지연 백엔드', '미디어 스트리밍 기초'],
    less_relevant_for: ['머신러닝 모델링', '결제 시스템'],
    profile_summary: '실시간·저지연 백엔드를 다뤄온 멘토',
  },
  kim: {
    name: '김나래',
    domain: ['Network', 'Infra'],
    keywords: ['networking', 'turn/stun', 'high performance'],
    score: 61,
    reason:
      '네트워크·인프라 관점에서 실시간 영상 전송의 병목을 함께 살펴볼 수 있습니다. 다만 영상 코덱·WebRTC 세부에는 직접 경험이 적습니다.',
    can_help: ['네트워크 병목 분석', '인프라 아키텍처', '고성능 트래픽 처리'],
    less_relevant_for: ['프론트엔드 애니메이션', 'UX 라이팅'],
    profile_summary: '네트워크와 고성능 인프라를 다루는 멘토',
  },
  lee: {
    name: '이채린',
    domain: ['AI', 'LLM'],
    keywords: ['rag', 'prompt', 'evaluation', 'langgraph'],
    score: 83,
    reason:
      'LLM 활용과 RAG 파이프라인 경험이 있어 AI 기능의 품질·평가 방법을 보완해 줄 수 있습니다.',
    can_help: ['RAG 설계', '프롬프트 구조화', 'LLM 평가 방법'],
    less_relevant_for: ['인프라 비용 최적화', '세일즈'],
    profile_summary: 'LLM 애플리케이션과 평가 설계에 강한 멘토',
  },
  park: {
    name: '박정우',
    domain: ['Product', 'UX'],
    keywords: ['user research', 'validation', 'mvp'],
    score: 72,
    reason:
      '사용자 문제 정의는 정리됐다는 점에서, 검증 단계로 넘어갈 때 사용자 리서치와 MVP 범위 조정을 도울 수 있습니다.',
    can_help: ['사용자 검증', 'MVP 범위 설정', '문제 정의 구체화'],
    less_relevant_for: ['저수준 성능 튜닝', '쿠버네티스 운영'],
    profile_summary: '프로덕트 검증과 UX 리서치를 돕는 멘토',
  },
};

const has = (text: string, words: string[]): boolean => {
  const t = text.toLowerCase();
  return words.some((w) => t.includes(w.toLowerCase()));
};

/** ERROR 시나리오 트리거 — useRecommend가 이 값을 보고 throw 한다 */
export const ERROR_TRIGGER = '강제에러';

export function isErrorTrigger(req: RecommendRequest): boolean {
  return has(req.project_text, [ERROR_TRIGGER, 'force-error']);
}

/** 입력에 따라 mock 응답을 고른다 */
export function mockRecommend(req: RecommendRequest): RecommendResponse {
  const text = `${req.project_text} ${req.clarify_answer ?? ''}`;

  // 2) 확인 질문에 답한 경우 → 약점 구체화 후 정상 추천
  if (req.clarify_answer && req.clarify_answer.trim()) {
    return {
      status: 'recommended',
      gaps: ['시스템 구조 검토', '확장성', '보안'],
      refined: false,
      mentors: [MENTORS.yoon, MENTORS.han, MENTORS.lee],
    };
  }

  // empty: 의미 없는/너무 추상적인 입력 (데모용 명시 키워드)
  if (has(text, ['없는멘토', 'asdf', 'qwer', '테스트빈결과'])) {
    return { status: 'recommended', gaps: ['불명확'], refined: true, mentors: [] };
  }

  // 3) WebRTC·실시간 → limited (정확히 맞는 멘토 부족, 재검색 후 제한적)
  if (has(text, ['webrtc', '실시간', '영상', 'rtc', '스트리밍'])) {
    return {
      status: 'limited',
      gaps: ['실시간 영상 처리', '미디어 서버', '네트워크'],
      mentors: [MENTORS.oh, MENTORS.kim],
      notice:
        '정확히 맞는 멘토가 부족해 근거가 제한적입니다. 실시간 시스템·네트워크 인접 영역의 멘토를 함께 제시합니다.',
    };
  }

  // 2) 구조·아키텍처·기획 → 확인 질문 1개
  if (has(text, ['구조', '아키텍처', '설계', '기획', '확신'])) {
    return {
      status: 'need_clarification',
      question:
        '지금 가장 걱정되는 부분은 성능·확장성·배포·보안 중 어디에 가깝나요?',
      options: ['성능', '확장성', '배포', '보안'],
    };
  }

  // 1) 배포·서빙·MLOps (기본 시나리오) → 정상 추천
  if (has(text, ['배포', '서빙', 'mlops', 'serving', 'deploy', '운영'])) {
    return {
      status: 'recommended',
      gaps: ['모델 서빙', 'MLOps', '배포 경험'],
      refined: false,
      mentors: [MENTORS.seo, MENTORS.jang],
    };
  }

  // 그 외 일반 입력 → AI/프로덕트 관점 추천 (항상 무언가 보여줌)
  return {
    status: 'recommended',
    gaps: ['AI 기능 설계', '사용자 검증'],
    refined: false,
    mentors: [MENTORS.lee, MENTORS.park],
  };
}
