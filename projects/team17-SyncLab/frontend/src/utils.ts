import type { RouteType } from "./types";

export const roles = ["기획자", "개발자", "디자이너", "PM", "팀 리드"];

export const communicationTypes = [
  "슬랙 메시지",
  "회의록",
  "기획서 일부",
  "이메일",
  "업무 요청 문장",
];

export function routeLabel(route?: RouteType) {
  switch (route) {
    case "need_more_context":
      return "보충 질문 생성";
    case "definition_enrichment":
      return "정의 보강 보고서";
    case "consensus_report":
    default:
      return "합의 필요 보고서";
  }
}

export function routeDescription(route?: RouteType) {
  switch (route) {
    case "need_more_context":
      return "화자 또는 수신자 정보가 부족해 추가 질문을 먼저 제공합니다.";
    case "definition_enrichment":
      return "내부 용어 정의가 부족해 의미 후보와 확인 질문을 함께 제공합니다.";
    case "consensus_report":
    default:
      return "오해 가능성이 높은 용어를 보고서 형태로 정리합니다.";
  }
}

export function riskClass(riskLevel: string) {
  if (riskLevel === "높음") return "bg-red-50 text-danger ring-red-100";
  if (riskLevel === "보통") return "bg-orange-50 text-warning ring-orange-100";
  return "bg-green-50 text-success ring-green-100";
}
