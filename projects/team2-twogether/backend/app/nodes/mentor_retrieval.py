from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from backend.app.core.env import DEFAULT_ENV_PATH, load_dotenv
from backend.app.rag.bm25_retriever import retrieve_bm25_rule_candidates
from backend.app.rag.mentor_vector_store import QdrantMentorVectorStore
from backend.app.rag.upstage_embeddings import UpstageEmbeddingClient


DEFAULT_MENTORS_PATH = Path(__file__).resolve().parents[3] / "data" / "mentors.json"
MATCH_FIELDS = ("keywords", "can_help", "domain", "profile_summary")
FIELD_WEIGHTS = {
    "keywords": 4.0,
    "can_help": 3.0,
    "domain": 2.0,
    "profile_summary": 1.0,
}
STOPWORDS = {
    "and",
    "or",
    "the",
    "for",
    "with",
    "quality",
    "based",
}


def build_search_query(gap_context: dict[str, Any]) -> str:
    values = [
        *gap_context.get("query_hints", []),
        *gap_context.get("needed_mentor_expertise", []),
        *gap_context.get("gap_categories", []),
        gap_context.get("main_gap", ""),
    ]
    query_parts = _unique_display_values(values)
    return " ".join(query_parts[:14])


def load_mentors(path: Path | None = None) -> list[dict[str, Any]]:
    mentors_path = path or DEFAULT_MENTORS_PATH
    if not mentors_path.exists():
        return []

    raw_content = mentors_path.read_text(encoding="utf-8").strip()
    if not raw_content:
        return []

    try:
        mentors = json.loads(raw_content)
    except json.JSONDecodeError:
        return []

    if not isinstance(mentors, list):
        return []
    return [mentor for mentor in mentors if isinstance(mentor, dict)]


def retrieve_mentor_candidates(
    gap_context: dict[str, Any],
    mentors: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    return retrieve_bm25_rule_candidates(gap_context, mentors, limit=limit)


def mentor_retrieval_node(state: dict[str, Any]) -> dict[str, Any]:
    gap_context = state.get("gap_context")
    if not gap_context:
        return {"search_query": "", "retrieved_mentors": []}

    search_query = state.get("refined_query") or build_search_query(gap_context)
    mentors = load_mentors()
    retrieval_mode = get_retrieval_mode(
        env_path=state.get("_env_path", DEFAULT_ENV_PATH),
        mode_override=state.get("retrieval_mode"),
    )

    if retrieval_mode == "vector":
        vector_candidates = _retrieve_vector_candidates(state, gap_context)
        return {
            "search_query": search_query,
            "retrieved_mentors": vector_candidates
            or retrieve_bm25_rule_candidates(
                gap_context,
                mentors,
                search_query=search_query,
            ),
        }

    if retrieval_mode == "hybrid":
        bm25_candidates = retrieve_bm25_rule_candidates(
            gap_context,
            mentors,
            search_query=search_query,
        )
        vector_candidates = _retrieve_vector_candidates(state, gap_context)
        if not vector_candidates:
            return {
                "search_query": search_query,
                "retrieved_mentors": bm25_candidates,
            }

        return {
            "search_query": search_query,
            "retrieved_mentors": merge_hybrid_candidates(
                bm25_candidates,
                vector_candidates,
            ),
        }

    return {
        "search_query": search_query,
        "retrieved_mentors": retrieve_bm25_rule_candidates(
            gap_context,
            mentors,
            search_query=search_query,
        ),
    }


def _retrieve_vector_candidates(
    state: dict[str, Any],
    gap_context: dict[str, Any],
) -> list[dict[str, Any]]:
    embedding_client = state.get("_embedding_client")
    vector_store = state.get("_vector_store")
    if embedding_client and vector_store:
        try:
            return retrieve_mentor_candidates_rag(
                gap_context,
                embedding_client=embedding_client,
                vector_store=vector_store,
                refined_query=state.get("refined_query"),
            )
        except (OSError, ValueError, KeyError, AssertionError):
            return []

    if _has_vector_config():
        try:
            return retrieve_mentor_candidates_rag(
                gap_context,
                embedding_client=UpstageEmbeddingClient.from_env(),
                vector_store=QdrantMentorVectorStore.from_env(),
                refined_query=state.get("refined_query"),
            )
        except (OSError, ValueError, KeyError):
            return []
    return []


def get_retrieval_mode(
    env_path=DEFAULT_ENV_PATH,
    mode_override: str | None = None,
) -> str:
    if mode_override:
        return _normalize_retrieval_mode(mode_override)

    load_dotenv(env_path)
    return _normalize_retrieval_mode(os.getenv("MENTOR_RETRIEVAL_MODE", "bm25"))


def retrieve_mentor_candidates_rag(
    gap_context: dict[str, Any],
    *,
    embedding_client: Any,
    vector_store: Any,
    limit: int = 5,
    refined_query: str | None = None,
) -> list[dict[str, Any]]:
    if not gap_context or limit <= 0:
        return []

    search_query = refined_query or build_search_query(gap_context)
    query_vector = embedding_client.embed_query(search_query)
    search_results = vector_store.search(query_vector, limit=limit)
    query_terms = _terms_for_matching(search_query)

    candidates = []
    for result in search_results:
        payload = result.get("payload", {})
        if not isinstance(payload, dict):
            continue

        candidates.append(
            {
                **payload,
                "retrieval_score": round(float(result.get("score", 0.0)), 4),
                "matched_keywords": _matched_payload_keywords(payload, query_terms),
                "matched_fields": ["mentor_document"],
                "retrieval_source": "vector",
            }
        )
    return candidates


def merge_hybrid_candidates(
    bm25_candidates: list[dict[str, Any]],
    vector_candidates: list[dict[str, Any]],
    *,
    limit: int = 5,
    bm25_weight: float = 0.45,
    vector_weight: float = 0.55,
) -> list[dict[str, Any]]:
    bm25_norm = _normalized_scores(bm25_candidates)
    vector_norm = _normalized_scores(vector_candidates)
    merged: dict[str, dict[str, Any]] = {}

    for candidate in bm25_candidates:
        key = _candidate_key(candidate)
        merged[key] = {
            **candidate,
            "retrieval_score": bm25_weight * bm25_norm.get(key, 0.0),
            "matched_keywords": list(candidate.get("matched_keywords", [])),
            "matched_fields": list(candidate.get("matched_fields", [])),
            "retrieval_source": "hybrid",
        }

    for candidate in vector_candidates:
        key = _candidate_key(candidate)
        if key not in merged:
            merged[key] = {
                **candidate,
                "retrieval_score": 0.0,
                "matched_keywords": [],
                "matched_fields": [],
                "retrieval_source": "hybrid",
            }

        merged_candidate = merged[key]
        merged_candidate["retrieval_score"] += (
            vector_weight * vector_norm.get(key, 0.0)
        )
        merged_candidate["matched_keywords"] = _unique_display_values(
            [
                *merged_candidate.get("matched_keywords", []),
                *candidate.get("matched_keywords", []),
            ]
        )
        merged_candidate["matched_fields"] = _unique_display_values(
            [
                *merged_candidate.get("matched_fields", []),
                *candidate.get("matched_fields", []),
            ]
        )
        merged_candidate["retrieval_source"] = "hybrid"

    ranked = sorted(
        merged.values(),
        key=lambda candidate: (-candidate["retrieval_score"], candidate.get("name", "")),
    )
    for candidate in ranked:
        candidate["retrieval_score"] = round(candidate["retrieval_score"], 4)
    return ranked[:limit]


def _score_mentor(
    mentor: dict[str, Any],
    gap_terms: set[str],
) -> tuple[float, list[str], list[str]]:
    score = 0.0
    matched_keywords: list[str] = []
    matched_fields: list[str] = []

    for field_name in MATCH_FIELDS:
        field_values = _field_values(mentor, field_name)
        field_matches = _matched_terms(field_values, gap_terms)
        if not field_matches:
            continue

        matched_fields.append(field_name)
        score += FIELD_WEIGHTS[field_name] * len(field_matches)
        matched_keywords.extend(_field_match_labels(field_name, field_values, gap_terms))

    return score, _unique_display_values(matched_keywords), matched_fields


def _has_vector_config() -> bool:
    load_dotenv()
    return bool(os.getenv("UPSTAGE_API_KEY") and os.getenv("QDRANT_URL"))


def _normalize_retrieval_mode(value: str) -> str:
    mode = value.strip().casefold()
    if mode in {"rag", "vector"}:
        return "vector"
    if mode == "hybrid":
        return "hybrid"
    return "bm25"


def _normalized_scores(candidates: list[dict[str, Any]]) -> dict[str, float]:
    if not candidates:
        return {}

    scores = {
        _candidate_key(candidate): float(candidate.get("retrieval_score", 0.0))
        for candidate in candidates
    }
    max_score = max(scores.values(), default=0.0)
    if max_score <= 0:
        return {key: 0.0 for key in scores}
    return {key: score / max_score for key, score in scores.items()}


def _candidate_key(candidate: dict[str, Any]) -> str:
    key = candidate.get("mentor_id") or candidate.get("name")
    if key:
        return str(key)
    return f"anonymous:{id(candidate)}"


def _matched_payload_keywords(
    payload: dict[str, Any],
    query_terms: set[str],
) -> list[str]:
    matched_keywords = []
    for field_name in MATCH_FIELDS:
        matched_keywords.extend(
            _field_match_labels(
                field_name,
                _field_values(payload, field_name),
                query_terms,
            )
        )
    return _unique_display_values(matched_keywords)


def _extract_gap_terms(gap_context: dict[str, Any]) -> set[str]:
    values = [
        gap_context.get("main_gap", ""),
        *gap_context.get("gap_categories", []),
        *gap_context.get("needed_mentor_expertise", []),
        *gap_context.get("query_hints", []),
    ]
    terms: set[str] = set()
    for value in values:
        terms.update(_terms_for_matching(str(value)))
    return terms


def _matched_terms(values: list[str], gap_terms: set[str]) -> set[str]:
    matched: set[str] = set()
    for value in values:
        value_terms = _terms_for_matching(value)
        for value_term in value_terms:
            for gap_term in gap_terms:
                if _terms_match(value_term, gap_term):
                    matched.add(value_term)
    return matched


def _field_match_labels(
    field_name: str,
    field_values: list[str],
    gap_terms: set[str],
) -> list[str]:
    labels: list[str] = []
    for value in field_values:
        value_terms = _terms_for_matching(value)
        if any(
            _terms_match(value_term, gap_term)
            for value_term in value_terms
            for gap_term in gap_terms
        ):
            labels.append(_normalize_label(value))

    if field_name == "keywords":
        return labels
    return [label for label in labels if len(label) > 1]


def _terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if len(left) >= 3 and left in right:
        return True
    return len(right) >= 3 and right in left


def _terms_for_matching(value: str) -> set[str]:
    normalized = _normalize_label(value)
    if not normalized:
        return set()

    terms = {normalized}
    terms.update(_split_terms(normalized))
    return {term for term in terms if term and term not in STOPWORDS}


def _split_terms(value: str) -> set[str]:
    raw_terms = re.split(r"[^0-9a-zA-Z가-힣+#/.-]+", value)
    return {
        term
        for term in raw_terms
        if len(term) >= 2 and term not in STOPWORDS
    }


def _field_values(mentor: dict[str, Any], field_name: str) -> list[str]:
    value = mentor.get(field_name, [])
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def _normalize_label(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


def _unique_display_values(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = _normalize_label(text)
        if not text or key in seen:
            continue
        result.append(text)
        seen.add(key)
    return result
