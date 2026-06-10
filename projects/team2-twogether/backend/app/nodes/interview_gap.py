import re
from dataclasses import dataclass

from backend.app.schemas.gap import GapContext, ParsedInput


@dataclass(frozen=True)
class GapRule:
    categories: tuple[str, ...]
    signals: tuple[str, ...]
    expertise: tuple[str, ...]
    query_hints: tuple[str, ...]


GAP_RULES: tuple[GapRule, ...] = (
    GapRule(
        categories=("RAG", "Embedding", "Retrieval"),
        signals=(
            "rag",
            "검색",
            "검색 품질",
            "검색 정확도",
            "임베딩",
            "embedding",
            "벡터",
            "vector",
            "유사도",
            "chunk",
            "청크",
            "retrieval",
        ),
        expertise=("RAG 검색 구조 설계", "임베딩 전략", "벡터 DB 활용"),
        query_hints=(
            "RAG",
            "retrieval quality",
            "embedding strategy",
            "vector database",
            "semantic search",
        ),
    ),
    GapRule(
        categories=("Agentic Workflow", "LangGraph", "LLM Orchestration"),
        signals=(
            "langgraph",
            "agent",
            "에이전트",
            "분기",
            "상태",
            "state",
            "workflow",
            "워크플로우",
            "orchestration",
        ),
        expertise=("LangGraph 구조 설계", "상태 기반 워크플로우 설계", "에이전트 분기 설계"),
        query_hints=(
            "LangGraph",
            "agent workflow",
            "LLM orchestration",
            "state management",
        ),
    ),
    GapRule(
        categories=("LLM Evaluation", "Prompt Engineering", "Recommendation"),
        signals=(
            "추천",
            "근거",
            "평가",
            "환각",
            "hallucination",
            "신뢰도",
            "적합도",
            "ranking",
            "rank",
            "프롬프트",
            "prompt",
        ),
        expertise=("LLM 평가", "추천 근거 생성", "프롬프트 설계"),
        query_hints=(
            "LLM evaluation",
            "recommendation system",
            "recommendation reasoning",
            "ranking",
            "hallucination mitigation",
            "prompt engineering",
        ),
    ),
    GapRule(
        categories=("Infra", "MLOps", "DevOps"),
        signals=(
            "배포",
            "운영",
            "서버",
            "docker",
            "도커",
            "서빙",
            "serving",
            "api",
            "latency",
            "지연",
            "인프라",
            "infra",
            "mlops",
        ),
        expertise=("배포 구조 설계", "모델 서빙", "운영 환경 구성"),
        query_hints=("deployment", "MLOps", "Docker", "model serving", "infrastructure"),
    ),
    GapRule(
        categories=("Architecture", "Backend", "Scalability"),
        signals=(
            "구조",
            "확장",
            "확장성",
            "백엔드",
            "backend",
            "api",
            "모듈",
            "성능",
            "architecture",
            "system design",
        ),
        expertise=("백엔드 아키텍처 리뷰", "API 설계", "확장성 검토"),
        query_hints=("backend architecture", "API design", "scalability", "system design"),
    ),
    GapRule(
        categories=("Product", "UX", "Research"),
        signals=(
            "사용자",
            "검증",
            "문제 정의",
            "ux",
            "화면",
            "기획",
            "데모",
            "product",
            "research",
        ),
        expertise=("사용자 검증", "문제 정의", "서비스 기획"),
        query_hints=("product strategy", "UX research", "user validation", "service design"),
    ),
)

CORE_QUALITY_CATEGORIES = {
    "RAG",
    "Retrieval",
    "Agentic Workflow",
    "LangGraph",
    "LLM Evaluation",
    "Recommendation",
}

RISK_SIGNALS = (
    "짧",
    "기간",
    "데모",
    "로컬",
    "합성",
    "제약",
    "부족",
    "초기",
    "마감",
)


def analyze_project_gap(parsed_input: ParsedInput | dict) -> GapContext:
    parsed = _to_parsed_input(parsed_input)
    scores = _score_rules(parsed)
    selected_rules = _select_rules(scores, parsed)

    if not selected_rules:
        selected_rules = _fallback_rules(parsed)

    gap_categories = _collect_ranked_values(
        selected_rules, "categories", limit=6
    )
    needed_mentor_expertise = _collect_ranked_values(
        selected_rules, "expertise", limit=4
    )
    query_hints = _unique(
        hint for rule in selected_rules for hint in rule.query_hints
    )[:12]
    matched_fields = _matched_source_fields(parsed, selected_rules)
    source_fields = list(matched_fields.keys())
    priority = _decide_priority(parsed, gap_categories, scores)

    return GapContext(
        main_gap=_build_main_gap(gap_categories, needed_mentor_expertise),
        gap_categories=gap_categories,
        needed_mentor_expertise=needed_mentor_expertise,
        priority=priority,
        reason=_build_reason(gap_categories, matched_fields),
        query_hints=query_hints,
        source_fields=source_fields,
    )


def interview_gap_node(state: dict) -> dict:
    parsed_input = state.get("parsed_input")
    if not _has_analyzable_input(parsed_input):
        return {"gap_context": None}

    gap_context = analyze_project_gap(parsed_input)
    return {"gap_context": gap_context.model_dump()}


def _to_parsed_input(parsed_input: ParsedInput | dict) -> ParsedInput:
    if isinstance(parsed_input, ParsedInput):
        return parsed_input
    return ParsedInput(**parsed_input)


def _has_analyzable_input(parsed_input: ParsedInput | dict | None) -> bool:
    if not parsed_input:
        return False

    parsed = _to_parsed_input(parsed_input)
    return any(
        (
            parsed.project_summary.strip(),
            parsed.concerns,
            parsed.user_goal.strip(),
        )
    )


def _score_rules(parsed: ParsedInput) -> dict[GapRule, int]:
    field_values = {
        "concerns": parsed.concerns,
        "user_goal": [parsed.user_goal],
        "tech_stack": parsed.tech_stack,
        "current_stage": [parsed.current_stage],
        "constraints": parsed.constraints,
        "domain": parsed.domain,
        "project_summary": [parsed.project_summary],
    }
    field_weights = {
        "concerns": 4,
        "user_goal": 1,
        "tech_stack": 2,
        "current_stage": 2,
        "constraints": 2,
        "domain": 1,
        "project_summary": 1,
    }

    scores: dict[GapRule, int] = {}
    for rule in GAP_RULES:
        score = 0
        for field_name, values in field_values.items():
            text = _join_text(values)
            if _contains_signal(text, rule.signals):
                score += field_weights[field_name]
        if score:
            scores[rule] = score
    return scores


def _select_rules(
    scores: dict[GapRule, int], parsed: ParsedInput
) -> tuple[GapRule, ...]:
    eligible_scores = {
        rule: score
        for rule, score in scores.items()
        if score >= 3
        or _first_matching_concern_index(parsed.concerns, rule) < len(parsed.concerns)
    }
    if not eligible_scores:
        eligible_scores = scores

    ranked = sorted(
        eligible_scores.items(),
        key=lambda item: (
            _first_matching_concern_index(parsed.concerns, item[0]),
            -item[1],
        ),
    )
    return tuple(rule for rule, _ in ranked[:3])


def _fallback_rules(parsed: ParsedInput) -> tuple[GapRule, ...]:
    if _has_enough_text_for_fallback(parsed):
        return (GAP_RULES[-1],)
    return ()


def _has_enough_text_for_fallback(parsed: ParsedInput) -> bool:
    text = _join_text(
        [
            parsed.project_summary,
            parsed.user_goal,
            parsed.current_stage,
            *parsed.concerns,
            *parsed.constraints,
            *parsed.domain,
        ]
    )
    return len(text.strip()) >= 20


def _first_matching_concern_index(concerns: list[str], rule: GapRule) -> int:
    for index, concern in enumerate(concerns):
        if _contains_signal(concern, rule.signals):
            return index
    return len(concerns) + 1


def _matched_source_fields(
    parsed: ParsedInput, selected_rules: tuple[GapRule, ...]
) -> dict[str, list[str]]:
    matched_fields: dict[str, list[str]] = {}
    rule_signals = tuple(
        signal for rule in selected_rules for signal in rule.signals
    )
    for field_name in (
        "concerns",
        "tech_stack",
        "current_stage",
        "constraints",
        "user_goal",
        "domain",
        "project_summary",
    ):
        values = _field_values(parsed, field_name)
        matched_values = [
            value for value in values if _contains_signal(value, rule_signals)
        ]
        if matched_values:
            matched_fields[field_name] = matched_values
    for field_name in ("current_stage", "constraints"):
        risk_values = [
            value
            for value in _field_values(parsed, field_name)
            if _contains_signal(value, RISK_SIGNALS)
        ]
        if risk_values:
            matched_fields.setdefault(field_name, [])
            matched_fields[field_name].extend(
                value for value in risk_values if value not in matched_fields[field_name]
            )
    return _sort_matched_fields(matched_fields)


def _decide_priority(
    parsed: ParsedInput, gap_categories: list[str], scores: dict[GapRule, int]
) -> str:
    top_score = max(scores.values(), default=0)
    has_core_quality_gap = any(
        category in CORE_QUALITY_CATEGORIES for category in gap_categories
    )
    has_risk_constraint = _contains_signal(
        _join_text([parsed.current_stage, *parsed.constraints]), RISK_SIGNALS
    )

    if top_score >= 6 and (has_core_quality_gap or has_risk_constraint):
        return "high"
    if top_score >= 3:
        return "medium"
    return "low"


def _build_main_gap(
    gap_categories: list[str], needed_mentor_expertise: list[str]
) -> str:
    if not gap_categories or not needed_mentor_expertise:
        return "프로젝트 약점 분석을 위한 문제 정의 구체화 필요"

    category_text = ", ".join(gap_categories[:2])
    expertise_text = " 및 ".join(needed_mentor_expertise[:2])
    return f"{category_text} 영역의 {expertise_text} 역량 부족"


def _build_reason(
    gap_categories: list[str], matched_fields: dict[str, list[str]]
) -> str:
    field_labels = {
        "concerns": "현재 고민",
        "tech_stack": "기술 스택",
        "current_stage": "진행 단계",
        "constraints": "제약 조건",
        "user_goal": "멘토링 목표",
        "domain": "프로젝트 도메인",
        "project_summary": "프로젝트 요약",
    }
    category_text = ", ".join(gap_categories)
    evidence = _format_evidence(matched_fields, field_labels)

    if evidence:
        return (
            f"{evidence}에서 관련 신호가 확인되어 "
            f"{category_text} 역량이 현재 멘토 검색의 핵심 기준으로 판단됩니다."
        )
    return (
        f"{category_text} 역량 보완이 멘토 검색의 우선 기준으로 판단됩니다."
    )


def _contains_signal(text: str, signals: tuple[str, ...]) -> bool:
    return any(_matches_signal(text, signal) for signal in signals)


def _matches_signal(text: str, signal: str) -> bool:
    if signal.isascii() and signal.replace(" ", "").isalnum():
        pattern = rf"(?<![A-Za-z0-9]){re.escape(signal)}(?![A-Za-z0-9])"
        return re.search(pattern, text, re.IGNORECASE) is not None
    return signal.casefold() in text.casefold()


def _join_text(values: list[str] | tuple[str, ...]) -> str:
    return " ".join(str(value) for value in values if value)


def _field_values(parsed: ParsedInput, field_name: str) -> list[str]:
    value = getattr(parsed, field_name)
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def _format_evidence(
    matched_fields: dict[str, list[str]], field_labels: dict[str, str]
) -> str:
    evidence_parts = []
    for field_name, values in list(matched_fields.items())[:5]:
        label = field_labels[field_name]
        value_text = ", ".join(values[:3])
        evidence_parts.append(f"{label} '{value_text}'")
    return ", ".join(evidence_parts)


def _sort_matched_fields(matched_fields: dict[str, list[str]]) -> dict[str, list[str]]:
    field_order = (
        "concerns",
        "current_stage",
        "constraints",
        "tech_stack",
        "user_goal",
        "domain",
        "project_summary",
    )
    return {
        field_name: matched_fields[field_name]
        for field_name in field_order
        if field_name in matched_fields
    }


def _unique(values) -> list[str]:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _collect_ranked_values(
    selected_rules: tuple[GapRule, ...], field_name: str, limit: int
) -> list[str]:
    primary_values = [
        getattr(rule, field_name)[0]
        for rule in selected_rules
        if getattr(rule, field_name)
    ]
    secondary_values = [
        value
        for rule in selected_rules
        for value in getattr(rule, field_name)[1:]
    ]
    return _unique([*primary_values, *secondary_values])[:limit]
