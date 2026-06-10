from __future__ import annotations

from typing import Any

from backend.app.rag.bm25_retriever import tokenize

# Reused helpers from mentor_retrieval: keeps the refined query consistent with
# how the retrieval stage builds and de-duplicates its base query.
from backend.app.nodes.mentor_retrieval import (
    _unique_display_values,
    build_search_query,
)


def query_refiner_node(state: dict[str, Any]) -> dict[str, Any]:
    gap_context = state.get("gap_context") or {}
    search_query = state.get("search_query", "")
    evaluated_mentors = state.get("evaluated_mentors") or []
    retry_count = state.get("retry_count", 0) + 1

    refined_query = refine_search_query(gap_context, search_query, evaluated_mentors)
    return {"refined_query": refined_query, "retry_count": retry_count}


def refine_search_query(
    gap_context: dict[str, Any],
    search_query: str,
    evaluated_mentors: list[dict[str, Any]],
) -> str:
    return _refine_query_rule_based(gap_context, search_query, evaluated_mentors)


def _refine_query_rule_based(
    gap_context: dict[str, Any],
    search_query: str,
    evaluated_mentors: list[dict[str, Any]],
) -> str:
    base_query = (search_query or "").strip()
    if not base_query and gap_context:
        base_query = build_search_query(gap_context)

    if not gap_context:
        return base_query

    used_tokens = set(tokenize(base_query))
    expansion_terms = [
        *gap_context.get("query_hints", []),
        *gap_context.get("needed_mentor_expertise", []),
        *gap_context.get("gap_categories", []),
    ]
    unused_terms = [
        term
        for term in expansion_terms
        if term and not _is_term_present(term, used_tokens)
    ]
    if not unused_terms:
        return base_query

    parts = _unique_display_values([base_query, *unused_terms])
    return " ".join(part for part in parts if part)


def _is_term_present(term: str, used_tokens: set[str]) -> bool:
    term_tokens = set(tokenize(str(term)))
    if not term_tokens:
        return False
    return term_tokens.issubset(used_tokens)


def _refine_query_llm(
    gap_context: dict[str, Any],
    search_query: str,
    evaluated_mentors: list[dict[str, Any]],
) -> str:
    raise NotImplementedError("LLM query refinement is not implemented yet")
