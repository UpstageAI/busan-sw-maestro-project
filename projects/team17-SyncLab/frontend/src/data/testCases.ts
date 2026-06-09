import type { TestCase } from "../types";

const sharedTerms = [
  {
    term: "도메인",
    context: "로그인 도메인",
    currentMeaning: "로그인 관련 기능 영역으로 추정됩니다.",
    plannerView: "로그인 기능 전체를 의미할 수 있습니다.",
    developerView: "인증 도메인 로직 또는 도메인 모델을 의미할 수 있습니다.",
    designerView: "로그인 화면 또는 사용자 흐름을 의미할 수 있습니다.",
    pmView: "로그인 관련 업무 범위를 의미할 수 있습니다.",
    riskLevel: "높음",
    riskReason: "도메인의 의미가 다르면 실제 구현 범위와 일정 산정이 달라질 수 있습니다.",
    confirmationQuestion:
      "여기서 말한 로그인 도메인은 로그인 기능 전체를 의미하나요, 아니면 백엔드 인증 로직을 의미하나요?",
  },
  {
    term: "정책 반영",
    context: "우선 정책만 반영",
    currentMeaning: "로그인 관련 정책을 우선 적용하자는 의미로 추정됩니다.",
    plannerView: "기획 문서에 정의된 정책을 반영하는 것으로 이해할 수 있습니다.",
    developerView: "권한, 예외 처리, 상태값 등의 실제 로직 구현으로 이해할 수 있습니다.",
    designerView: "정책에 맞는 화면 상태나 문구를 반영하는 것으로 이해할 수 있습니다.",
    pmView: "전체 구현 전에 우선 처리할 최소 작업 범위로 이해할 수 있습니다.",
    riskLevel: "높음",
    riskReason: "문서 수정인지 실제 기능 구현인지에 따라 작업 결과물이 달라질 수 있습니다.",
    confirmationQuestion:
      "정책 반영은 기획 문서 수정인가요, 아니면 실제 권한/상태 로직 구현까지 포함하나요?",
  },
];

export const testCases: TestCase[] = [
  {
    id: "US-01",
    scenarioName: "Slack 요청 전 모호한 표현 점검",
    primaryUser: "PM/기획자",
    route: "consensus_report",
    request: {
      text: "이번 주 안에 로그인 도메인 쪽 디벨롭 가능할까요? 공수 크면 우선 정책만 반영해도 됩니다.",
      senderRole: "기획자",
      receiverRole: "개발자",
      communicationType: "슬랙 메시지",
    },
    response: {
      route: "consensus_report",
      summary: "로그인 관련 작업 가능 여부와 우선 반영 범위를 확인하는 메시지입니다.",
      keyRequest:
        "이번 주 안에 로그인 관련 작업이 가능한지 확인하고, 공수가 크면 정책 반영만 우선 진행하려는 요청입니다.",
      terms: sharedTerms,
      agreementQuestions: [
        "여기서 말한 로그인 도메인은 로그인 기능 전체를 의미하나요, 아니면 백엔드 인증 로직을 의미하나요?",
        "정책 반영은 기획 문서 수정인가요, 아니면 실제 권한/상태 로직 구현까지 포함하나요?",
        "공수는 개발 시간만 의미하나요, 아니면 기획·디자인·QA를 포함한 전체 작업량을 의미하나요?",
      ],
      checklist: [
        "로그인 작업 범위를 먼저 확정한다.",
        "정책 반영의 기준이 문서인지 실제 구현인지 확인한다.",
        "공수 산정 범위에 포함되는 역할을 확인한다.",
        "이번 주 안에 완료해야 하는 최소 결과물을 합의한다.",
      ],
    },
  },
  {
    id: "US-02",
    scenarioName: "회의록에서 도메인/아티팩트 충돌 탐지",
    primaryUser: "PM, 개발자, 디자이너",
    route: "consensus_report",
    request: {
      text: "PM: 이번 도메인은 결제 쪽으로 잡죠. Dev: 도메인 모델이 아직 필요해요. Designer: 결제 도메인 화면 아티팩트를 공유할게요.",
      senderRole: "PM",
      receiverRole: "개발자",
      communicationType: "회의록",
    },
    response: {
      route: "consensus_report",
      summary: "결제 관련 회의에서 도메인과 아티팩트의 의미가 직군별로 다르게 사용되었습니다.",
      keyRequest: "결제 업무 범위와 산출물 기준을 업무 착수 전에 다시 맞춰야 합니다.",
      terms: [
        {
          ...sharedTerms[0],
          term: "도메인",
          context: "결제 도메인 / 도메인 모델",
          currentMeaning: "결제 기능 영역 또는 도메인 모델을 의미할 수 있습니다.",
          confirmationQuestion:
            "이번 회의에서 도메인은 결제 기능 범위인가요, 코드의 도메인 모델인가요?",
        },
        {
          term: "아티팩트",
          context: "화면 아티팩트",
          currentMeaning: "디자인 시안 또는 프로젝트 산출물로 추정됩니다.",
          plannerView: "정책 문서와 회의 결과물을 포함한 산출물로 이해할 수 있습니다.",
          developerView: "빌드 결과물이나 배포 산출물로 이해할 수 있습니다.",
          designerView: "화면 시안, 프로토타입, 컴포넌트 에셋으로 이해할 수 있습니다.",
          pmView: "업무 진행을 확인할 수 있는 전체 산출물로 이해할 수 있습니다.",
          riskLevel: "높음",
          riskReason: "산출물 범위가 다르면 리뷰 대상과 완료 기준이 달라집니다.",
          confirmationQuestion:
            "여기서 아티팩트는 디자인 시안만 의미하나요, 정책 문서와 개발 산출물도 포함하나요?",
        },
      ],
      agreementQuestions: [
        "이번 회의에서 도메인은 기능 범위인가요, 도메인 모델인가요?",
        "아티팩트의 완료 기준은 디자인 시안 공유인가요, 문서와 개발 산출물까지 포함하나요?",
      ],
      checklist: [
        "도메인이라는 표현의 기준을 기능/코드 관점으로 분리한다.",
        "아티팩트의 포함 범위를 확정한다.",
        "완료 기준을 회의록에 남긴다.",
      ],
    },
  },
  {
    id: "US-03",
    scenarioName: "기술적 컨텍스트와 사용자 컨텍스트 구분",
    primaryUser: "개발자, PM",
    route: "consensus_report",
    request: {
      text: "React Context 쪽 이슈로 보이는데, 사용자 컨텍스트를 보면 결제 직전에 이탈합니다.",
      senderRole: "개발자",
      receiverRole: "PM",
      communicationType: "업무 요청 문장",
    },
    response: {
      route: "consensus_report",
      summary: "컨텍스트가 기술 API와 사용자 상황이라는 두 의미로 함께 사용되었습니다.",
      keyRequest: "기술적 원인 분석과 사용자 행동 분석을 구분해 논의해야 합니다.",
      terms: [
        {
          term: "컨텍스트",
          context: "React Context / 사용자 컨텍스트",
          currentMeaning: "React API 또는 사용자 상황을 의미할 수 있습니다.",
          plannerView: "사용자 상황과 문제 배경으로 이해할 수 있습니다.",
          developerView: "React 상태 전달 API로 이해할 수 있습니다.",
          designerView: "사용자 흐름과 화면 맥락으로 이해할 수 있습니다.",
          pmView: "문제 발생 배경과 의사결정 기준으로 이해할 수 있습니다.",
          riskLevel: "높음",
          riskReason: "기술 이슈와 사용자 문제를 구분하지 않으면 해결 방향이 달라집니다.",
          confirmationQuestion:
            "여기서 컨텍스트는 React Context API를 의미하나요, 사용자의 결제 상황을 의미하나요?",
        },
      ],
      agreementQuestions: [
        "이 이슈의 1차 원인은 React Context 구조인가요, 사용자 결제 흐름인가요?",
      ],
      checklist: [
        "기술 원인과 사용자 상황을 별도 항목으로 분리한다.",
        "각 항목의 담당자를 지정한다.",
      ],
    },
  },
  {
    id: "US-04",
    scenarioName: "화자 정보 부족으로 보충 질문 생성",
    primaryUser: "모든 사용자",
    route: "need_more_context",
    request: {
      text: "이번 아티팩트는 러프하게 잡고 다음 주에 디벨롭합시다.",
      senderRole: "",
      receiverRole: "",
      communicationType: "업무 요청 문장",
    },
    response: {
      route: "need_more_context",
      summary: "발화자와 수신자 직군 정보가 부족해 의미를 확정하기 어렵습니다.",
      keyRequest: "분석 정확도를 높이려면 최소한 발화자와 수신자 직군이 필요합니다.",
      terms: [],
      agreementQuestions: [
        "이 문장을 말한 사람의 직군은 무엇인가요?",
        "수신자는 개발자, 디자이너, PM 중 누구인가요?",
        "아티팩트는 디자인 산출물인가요, 문서 또는 개발 산출물인가요?",
      ],
      checklist: [
        "발화자 직군을 입력한다.",
        "수신자 직군을 입력한다.",
        "아티팩트의 대상 산출물을 선택한다.",
      ],
    },
  },
  {
    id: "US-05",
    scenarioName: "디자인 아티팩트 범위 합의",
    primaryUser: "디자이너, PM",
    route: "consensus_report",
    request: {
      text: "이번 디자인 아티팩트는 와이어프레임만 보면 될까요, 프로토타입까지 필요할까요?",
      senderRole: "디자이너",
      receiverRole: "PM",
      communicationType: "슬랙 메시지",
    },
    response: {
      route: "consensus_report",
      summary: "디자인 산출물의 범위와 완료 기준을 확인하는 메시지입니다.",
      keyRequest: "와이어프레임과 프로토타입 중 어떤 산출물이 필요한지 합의해야 합니다.",
      terms: [
        {
          term: "아티팩트",
          context: "디자인 아티팩트",
          currentMeaning: "와이어프레임 또는 프로토타입을 의미할 수 있습니다.",
          plannerView: "의사결정에 필요한 산출물로 이해할 수 있습니다.",
          developerView: "구현 참고 자료로 이해할 수 있습니다.",
          designerView: "화면 설계안 또는 인터랙션 프로토타입으로 이해할 수 있습니다.",
          pmView: "일정과 승인 기준이 되는 결과물로 이해할 수 있습니다.",
          riskLevel: "높음",
          riskReason: "필요 산출물이 달라지면 작업량과 리뷰 기준이 달라집니다.",
          confirmationQuestion:
            "디자인 아티팩트는 와이어프레임만 의미하나요, 클릭 가능한 프로토타입까지 포함하나요?",
        },
      ],
      agreementQuestions: [
        "이번 산출물은 와이어프레임만 필요한가요, 프로토타입까지 필요한가요?",
      ],
      checklist: [
        "필요 산출물의 수준을 정한다.",
        "리뷰 기준과 제출 일정을 정한다.",
      ],
    },
  },
  {
    id: "US-06",
    scenarioName: "판교식 표현을 업무 기준으로 구체화",
    primaryUser: "PM, 팀 리드",
    route: "consensus_report",
    request: {
      text: "이 이슈는 퀵하게 정리하고 러프하게 디벨롭해서 다음 싱크 때 봅시다.",
      senderRole: "PM",
      receiverRole: "팀 리드",
      communicationType: "회의록",
    },
    response: {
      route: "consensus_report",
      summary: "퀵하게, 러프하게, 디벨롭, 싱크처럼 기준이 불명확한 표현이 포함되었습니다.",
      keyRequest: "작업 수준과 일정 기준을 구체적인 완료 조건으로 바꿔야 합니다.",
      terms: [
        {
          term: "퀵하게",
          context: "퀵하게 정리",
          currentMeaning: "빠르게 초안을 만들자는 의미로 추정됩니다.",
          plannerView: "오늘 중 간단 정리로 이해할 수 있습니다.",
          developerView: "임시 구현 또는 빠른 기술 검토로 이해할 수 있습니다.",
          designerView: "낮은 충실도의 초안으로 이해할 수 있습니다.",
          pmView: "다음 회의 전까지 볼 수 있는 상태로 이해할 수 있습니다.",
          riskLevel: "보통",
          riskReason: "구체적인 마감과 완성도 기준이 없어 기대치가 달라질 수 있습니다.",
          confirmationQuestion:
            "퀵하게는 오늘 중 초안을 의미하나요, 다음 회의 전까지 공유 가능한 수준을 의미하나요?",
        },
      ],
      agreementQuestions: [
        "러프하게의 완성도 기준은 어느 정도인가요?",
        "다음 싱크 전까지 필요한 결과물은 문서인가요, 구현물인가요?",
      ],
      checklist: [
        "마감 시간을 명확히 정한다.",
        "초안과 구현물의 기준을 구분한다.",
      ],
    },
  },
  {
    id: "US-07",
    scenarioName: "내부 용어 정의 부족 확인",
    primaryUser: "모든 사용자",
    route: "definition_enrichment",
    request: {
      text: "이번 스펙은 내부 정책 기준으로 상태값만 맞추면 됩니다.",
      senderRole: "PM",
      receiverRole: "개발자",
      communicationType: "기획서 일부",
    },
    response: {
      route: "definition_enrichment",
      summary: "스펙, 내부 정책, 상태값의 조직 내부 정의가 부족합니다.",
      keyRequest: "내부 용어 정의를 보강한 뒤 구현 범위를 확정해야 합니다.",
      terms: [
        {
          term: "상태값",
          context: "상태값만 맞추면 됩니다",
          currentMeaning: "사용자 또는 업무 처리 상태를 나타내는 값으로 추정됩니다.",
          plannerView: "기획 정책에 정의된 사용자 상태로 이해할 수 있습니다.",
          developerView: "DB enum, API 응답 값, 프론트 상태값으로 이해할 수 있습니다.",
          designerView: "화면에 표시되는 상태 문구로 이해할 수 있습니다.",
          pmView: "업무 흐름의 진행 상태로 이해할 수 있습니다.",
          riskLevel: "보통",
          riskReason: "상태값의 출처와 기준이 다르면 구현과 화면 표시가 어긋납니다.",
          confirmationQuestion:
            "상태값은 DB/API 기준인가요, 화면에 표시되는 사용자 상태 문구인가요?",
        },
      ],
      agreementQuestions: [
        "내부 정책 문서에서 상태값 정의를 확인할 수 있나요?",
        "상태값 기준은 DB, API, 화면 중 어디인가요?",
      ],
      checklist: [
        "내부 정책 문서 위치를 확인한다.",
        "상태값의 기준 시스템을 정한다.",
      ],
    },
  },
];
