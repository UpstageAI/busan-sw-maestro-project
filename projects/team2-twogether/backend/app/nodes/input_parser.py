from __future__ import annotations

from typing import Any

from backend.app.graph.state import GraphState


_TECH_KEYWORDS: frozenset[str] = frozenset({
    "python", "java", "kotlin", "swift", "go", "rust",
    "react", "vue", "angular", "next", "svelte",
    "node", "express", "django", "fastapi", "spring", "flask", "rails",
    "api", "rest", "graphql", "grpc",
    "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "서버", "백엔드", "프론트", "앱", "웹", "모바일",
    "머신러닝", "딥러닝", "ai", "ml", "llm", "gpt",
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
})

_CONCERN_KEYWORDS: tuple[str, ...] = (
    "어렵", "모르", "부족", "고민", "문제", "개선", "도움", "막히",
    "어떻게", "힘들", "필요", "배우", "못", "안 됨", "안됨",
    "이슈", "오류", "에러", "error", "issue",
)


def _check_sufficiency_rule_based(
    project_text: str,
    tech_stack: list[str],
) -> tuple[bool, str, list[str]]:
    """Returns (is_sufficient, question, options)."""
    text_lower = project_text.lower()

    if len(project_text.strip()) < 30 and not tech_stack:
        return (
            False,
            "어떤 프로젝트를 만들고 있는지 조금 더 설명해 주실 수 있나요?",
            ["웹/앱 서비스", "데이터 분석/ML", "API 서버/백엔드", "기타"],
        )

    has_tech = bool(tech_stack) or any(kw in text_lower for kw in _TECH_KEYWORDS)
    has_concern = any(kw in project_text for kw in _CONCERN_KEYWORDS)

    if not has_tech:
        return (
            False,
            "어떤 기술 스택을 사용하고 있나요?",
            ["Python / Django / FastAPI", "JavaScript / React / Node.js", "Java / Spring", "기타 또는 아직 미정"],
        )

    if not has_concern:
        return (
            False,
            "현재 어떤 부분에서 멘토의 도움이 필요한가요?",
            ["설계 및 아키텍처", "특정 기술 구현", "성능 최적화", "프로젝트 방향 및 기획"],
        )

    return True, "", []


def _check_sufficiency_llm(
    project_text: str,
    tech_stack: list[str],
) -> tuple[bool, str, list[str]]:
    """LLM-based sufficiency check. Swap in when LLM integration is ready."""
    raise NotImplementedError


def _merge_clarify_answer(project_text: str, clarify_answer: str) -> str:
    return f"{project_text}\n추가 정보: {clarify_answer}"


_TECH_EXTRACT_MAP: dict[str, str] = {
    "python": "Python", "java": "Java", "kotlin": "Kotlin",
    "react": "React", "vue": "Vue", "angular": "Angular", "next": "Next.js",
    "node": "Node.js", "django": "Django", "fastapi": "FastAPI",
    "spring": "Spring", "flask": "Flask",
    "docker": "Docker", "aws": "AWS", "gcp": "GCP", "azure": "Azure",
    "mysql": "MySQL", "postgresql": "PostgreSQL", "mongodb": "MongoDB",
    "redis": "Redis", "llm": "LLM", "gpt": "GPT",
}

_DOMAIN_MAP: dict[str, str] = {
    "여행": "여행", "일정": "여행", "관광": "여행",
    "의료": "의료/헬스케어", "건강": "의료/헬스케어", "병원": "의료/헬스케어",
    "교육": "교육", "학습": "교육", "강의": "교육",
    "금융": "금융/핀테크", "결제": "금융/핀테크", "투자": "금융/핀테크",
    "쇼핑": "이커머스", "주문": "이커머스", "배달": "이커머스",
    "게임": "게임", "소셜": "소셜/커뮤니티", "커뮤니티": "소셜/커뮤니티",
}

_CONCERN_EXTRACT_KEYWORDS: tuple[str, ...] = (
    "어렵", "모르", "부족", "고민", "문제", "개선", "막히", "힘들",
)

_CONSTRAINT_KEYWORDS: tuple[str, ...] = (
    "1인", "혼자", "마감", "예산", "팀원 없", "기간",
)

_GOAL_KEYWORDS: tuple[str, ...] = (
    "원한다", "바란다", "기대", "필요", "도움", "배우고", "개선하고", "하고 싶",
)


def _parse_to_structured_rule_based(
    project_text: str,
    tech_stack: list[str],
    stage: str,
) -> dict[str, Any]:
    lines = [ln.strip() for ln in project_text.strip().splitlines() if ln.strip()]
    sentences = [s.strip() for s in project_text.replace(".", ".\n").splitlines() if s.strip()]

    project_summary = lines[0][:100] if lines else project_text[:100]

    text_lower = project_text.lower()
    extracted_tech: list[str] = list(tech_stack)
    for kw, label in _TECH_EXTRACT_MAP.items():
        if kw in text_lower and label not in extracted_tech:
            extracted_tech.append(label)

    concerns = [s for s in sentences if any(kw in s for kw in _CONCERN_EXTRACT_KEYWORDS)]

    seen_domains: set[str] = set()
    domains: list[str] = []
    for kw, domain in _DOMAIN_MAP.items():
        if kw in project_text and domain not in seen_domains:
            domains.append(domain)
            seen_domains.add(domain)

    constraints = [s for s in sentences if any(kw in s for kw in _CONSTRAINT_KEYWORDS)]

    user_goal = ""
    for sentence in reversed(sentences):
        if any(kw in sentence for kw in _GOAL_KEYWORDS):
            user_goal = sentence
            break
    if not user_goal:
        user_goal = lines[-1] if lines else ""

    return {
        "project_summary": project_summary,
        "tech_stack": extracted_tech,
        "current_stage": stage or "미정",
        "concerns": concerns,
        "domain": domains,
        "constraints": constraints,
        "user_goal": user_goal,
    }


def _parse_to_structured_llm(
    project_text: str,
    tech_stack: list[str],
    stage: str,
) -> dict[str, Any]:
    """LLM-based structured parser. Swap in when LLM integration is ready."""
    raise NotImplementedError


def parse_input(state: GraphState) -> GraphState:
    """Input Parser node."""
    project_text: str = state.get("user_input", "")  # type: ignore[arg-type]
    tech_stack: list[str] = state.get("tech_stack", [])  # type: ignore[arg-type]
    stage: str = state.get("stage", "")  # type: ignore[arg-type]
    clarify_answer: str | None = state.get("clarify_answer")  # type: ignore[arg-type]

    if clarify_answer:
        merged = _merge_clarify_answer(project_text, clarify_answer)
        return {
            **state,
            "user_input": merged,
            "is_input_sufficient": True,
            "clarification_question": "",
            "clarification_options": [],
            "parsed_input": _parse_to_structured_rule_based(merged, tech_stack, stage),
        }

    is_sufficient, question, options = _check_sufficiency_rule_based(project_text, tech_stack)

    if not is_sufficient:
        return {
            **state,
            "is_input_sufficient": False,
            "clarification_question": question,
            "clarification_options": options,
            "parsed_input": {},
        }

    return {
        **state,
        "is_input_sufficient": True,
        "clarification_question": "",
        "clarification_options": [],
        "parsed_input": _parse_to_structured_rule_based(project_text, tech_stack, stage),
    }
