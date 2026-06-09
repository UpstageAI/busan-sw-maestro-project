import operator
from typing import Annotated
from typing_extensions import TypedDict


class GraphState(TypedDict):
    # 입력
    input_text: str
    sender_role: str
    receiver_roles: list[str]
    communication_type: str

    # Phase 1 — context_intake
    context_analysis: dict
    summary: str
    key_request: str

    # Phase 2 — word_extractor (판단 없이 내용어 전체 추출)
    extracted_words: list[dict]
    # [{ "word": str, "context_snippet": str }, ...]

    # Phase 3 — role_worker 병렬 누적
    role_interpretations: Annotated[list, operator.add]
    # [{ "role": str, "words": [{ "word": str, "meaning": str }] }, ...]

    # Phase 4 — risk_term (직군 간 해석 비교 → 위험 용어 선별)
    risk_terms: list[dict]
    # [{ "term": str, "context_snippet": str, "interpretations": { role: meaning } }, ...]

    # Phase 5 — synthesis
    terms_with_risk: list[dict]
    agreement_questions: list[str]
    checklist: list[str]

    # Phase 6 — report (최종 응답)
    final_report: dict


class WorkerState(TypedDict):
    """fan-out 시 각 role_worker에 전달되는 서브 상태"""
    role: str
    extracted_words: list[dict]
    input_text: str
    sender_role: str
    receiver_roles: list[str]
