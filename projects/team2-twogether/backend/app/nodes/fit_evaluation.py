from __future__ import annotations

from typing import Any

from backend.app.rag.bm25_retriever import score_rule_matches

# Reused private helpers from mentor_retrieval. They are intentionally shared
# here to avoid duplicating retrieval/normalization logic; candidates for
# promotion to a public utility module if reuse grows further.
from backend.app.nodes.mentor_retrieval import (
    _candidate_key,
    _extract_gap_terms,
    _normalized_scores,
    _terms_for_matching,
    _terms_match,
)

CONFIDENCE_THRESHOLD = 60.0
RETRIEVAL_WEIGHT = 0.6
RULE_WEIGHT = 0.4
LESS_RELEVANT_PENALTY = 10.0


def fit_evaluation_node(state: dict[str, Any]) -> dict[str, Any]:
    gap_context = state.get("gap_context")
    retrieved_mentors = state.get("retrieved_mentors") or []
    if not gap_context or not retrieved_mentors:
        return {"evaluated_mentors": [], "is_recommendation_confident": False}

    evaluated_mentors = evaluate_mentor_fit(gap_context, retrieved_mentors)
    is_confident = bool(evaluated_mentors) and (
        max(mentor["score"] for mentor in evaluated_mentors) >= CONFIDENCE_THRESHOLD
    )
    return {
        "evaluated_mentors": evaluated_mentors,
        "is_recommendation_confident": is_confident,
    }


def evaluate_mentor_fit(
    gap_context: dict[str, Any],
    retrieved_mentors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not gap_context or not retrieved_mentors:
        return []

    gap_terms = _extract_gap_terms(gap_context)
    norm_retrieval = _normalized_scores(retrieved_mentors)
    norm_rule = _normalized_rule_scores(retrieved_mentors, gap_terms)

    evaluated: list[dict[str, Any]] = []
    for mentor in retrieved_mentors:
        key = _candidate_key(mentor)
        score = _score_fit_rule_based(
            mentor,
            norm_retrieval.get(key, 0.0),
            norm_rule.get(key, 0.0),
            gap_terms,
        )
        evaluated.append(_build_evaluated_mentor(mentor, score, gap_context))

    evaluated.sort(key=lambda item: (-item["score"], item.get("name", "")))
    return evaluated


def _build_evaluated_mentor(
    mentor: dict[str, Any],
    score: float,
    gap_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": mentor.get("name", ""),
        "domain": list(mentor.get("domain", []))
        if isinstance(mentor.get("domain"), list)
        else [mentor.get("domain")] if mentor.get("domain") else [],
        "score": score,
        "reason": _build_reason(mentor, gap_context),
        "matched_keywords": list(mentor.get("matched_keywords", [])),
        # Internal fields preserved for the downstream result_builder.
        "mentor_id": mentor.get("mentor_id", ""),
        "can_help": list(mentor.get("can_help", []))
        if isinstance(mentor.get("can_help"), list)
        else [],
        "less_relevant_for": list(mentor.get("less_relevant_for", []))
        if isinstance(mentor.get("less_relevant_for"), list)
        else [],
        "profile_summary": mentor.get("profile_summary", ""),
        "retrieval_score": mentor.get("retrieval_score", 0.0),
    }


def _score_fit_rule_based(
    mentor: dict[str, Any],
    norm_retrieval: float,
    norm_rule: float,
    gap_terms: set[str],
) -> float:
    base = 100.0 * (RETRIEVAL_WEIGHT * norm_retrieval + RULE_WEIGHT * norm_rule)
    penalty = LESS_RELEVANT_PENALTY if _has_less_relevant_overlap(mentor, gap_terms) else 0.0
    return max(0.0, min(100.0, round(base - penalty, 1)))


def _has_less_relevant_overlap(mentor: dict[str, Any], gap_terms: set[str]) -> bool:
    values = mentor.get("less_relevant_for", [])
    if not isinstance(values, list):
        return False
    for value in values:
        value_terms = _terms_for_matching(str(value))
        if any(
            _terms_match(value_term, gap_term)
            for value_term in value_terms
            for gap_term in gap_terms
        ):
            return True
    return False


def _build_reason(mentor: dict[str, Any], gap_context: dict[str, Any]) -> str:
    """Compose a reason from strings that actually exist in the data.

    Hallucination guard: no new facts are invented; f-strings only splice
    verbatim mentor/gap values.
    """
    mentor_evidence = _mentor_evidence(mentor)
    gap_evidence = _gap_evidence(gap_context)

    if mentor_evidence and gap_evidence:
        return (
            f"{gap_evidence} 약점과 직접 연결되는 "
            f"'{mentor_evidence}' 경험을 보유"
        )

    profile_summary = str(mentor.get("profile_summary", "")).strip()
    if profile_summary:
        return profile_summary
    return "프로필 정보를 기반으로 한 멘토 후보"


def _mentor_evidence(mentor: dict[str, Any]) -> str:
    matched_keywords = mentor.get("matched_keywords", [])
    if isinstance(matched_keywords, list) and matched_keywords:
        return str(matched_keywords[0])

    for field_name in ("can_help", "keywords"):
        values = mentor.get(field_name, [])
        if isinstance(values, list) and values:
            return str(values[0])
    return ""


def _gap_evidence(gap_context: dict[str, Any]) -> str:
    for field_name in ("gap_categories", "needed_mentor_expertise"):
        values = gap_context.get(field_name, [])
        if isinstance(values, list) and values:
            return str(values[0])
    return ""


def _normalized_rule_scores(
    candidates: list[dict[str, Any]],
    gap_terms: set[str],
) -> dict[str, float]:
    scores = {}
    for candidate in candidates:
        rule_score, _, _ = score_rule_matches(candidate, gap_terms)
        scores[_candidate_key(candidate)] = float(rule_score)
    return _max_normalize(scores)


def _max_normalize(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    max_score = max(scores.values(), default=0.0)
    if max_score <= 0:
        return {key: 0.0 for key in scores}
    return {key: score / max_score for key, score in scores.items()}


def _evaluate_fit_llm(
    gap_context: dict[str, Any],
    retrieved_mentors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raise NotImplementedError("LLM fit evaluation is not implemented yet")
