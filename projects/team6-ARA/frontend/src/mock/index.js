// 목데이터 통합 파일
// 실제 API가 연결되면 각 섹션의 교체 조건을 참고해 제거한다.

// ===== Agent 실행 로그 (BE 파이프라인이 로그를 반환하면 교체 — 현재 BE 미지원) =====
export const mockAgentLog = [
    { label: "맥락 로드",       warn: false },
    { label: "입력 유형 판단",  sub: "회의록", warn: false },
    { label: "분해",            sub: "8항목",  warn: false },
    { label: "분류",            warn: false },
    { label: "선호·지침 반영",  warn: false },
    { label: "완성도 검사",     warn: false },
    { label: "Tool 라우팅",     warn: false },
    { label: "중복·충돌 검증",  sub: "충돌 1·중복 1", warn: true },
    { label: "승인 대기",       warn: false },
];

// ===== 선호 후보 폴백 (BE /feedback/analyze 실데이터 우선, 수정 항목 없을 때만 사용) =====
export const mockPreferenceCandidates = [
    {
        field: "date_vague_to_pending",
        rule: "'다음 주쯤' 같은 모호한 날짜는 등록 대신 Pending으로 보류",
        basis: "사용자가 「멘토 시연」을 일정 등록하지 않고 보류 유지함",
    },
    {
        field: "memo_to_task",
        rule: "'기획서 다시 보기'류 항목은 메모가 아니라 할 일로 분류",
        basis: "Agent가 메모로 분류 → 사용자가 할 일로 수정",
    },
    {
        field: "calendar_default_duration",
        rule: "시작시간만 있는 회의는 기본 1시간으로 추정",
        basis: "「최종 리허설」의 '추정 1시간'을 사용자가 그대로 승인",
    },
];

// ===== 저장소 (GET /storage/{kind} 실데이터 우선, API 실패 시 폴백) =====
// preferences 탭은 BE에 대응 엔드포인트 없으므로 항상 이 목데이터 사용
export const mockStore = {
    tasks: [
        { id: 1, title: "발표자료 만들기",  assignee: "박성종", due: "06-04(목)", priority: "high",   status: "진행 전" },
        { id: 2, title: "API 테스트 정리",  assignee: "이동근", due: "06-04(목)", priority: "medium", status: "진행 전", note: "중복→새로 생성" },
        { id: 3, title: "데모 영상 준비",   assignee: "이우태", due: "06-04(목)", priority: "medium", status: "진행 전" },
        { id: 4, title: "기획서 다시 보기", assignee: "임재현", due: "06-04(목)", priority: "medium", status: "진행 전", note: "메모→할일" },
    ],
    calendar: [
        { id: 1, title: "멘토 미팅",    date: "06-05(금)", time: "10:00–11:00", assignee: "팀 전체", seed: true },
        { id: 2, title: "최종 리허설",  date: "06-05(금)", time: "11:00–12:00", assignee: "팀 전체", note: "충돌 해결로 이동" },
        { id: 3, title: "팀 점심",      date: "06-05(금)", time: null,          assignee: "팀 전체", allDay: true },
    ],
    memo: [],
    risk: [
        { id: 1, title: "캘린더 연동 실패 가능", mitigation: "Mock으로 대체", source: "안 되면 캘린더 연동은 Mock으로 대체하자" },
    ],
    pending: [
        { id: 1, title: "멘토님께 시연", reason: "모호 일정", question: "멘토 시연의 구체적 날짜/시간이 정해져 있나요?" },
    ],
};
