from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

K1 = 1.5
B = 0.75
TOKEN_PATTERN = re.compile(r"[0-9a-zA-Z가-힣+#/.-]+")
STOPWORDS = {
    "and",
    "or",
    "the",
    "for",
    "with",
    "quality",
    "based",
}
MATCH_FIELDS = ("keywords", "can_help", "domain", "profile_summary")
FIELD_WEIGHTS = {
    "keywords": 4.0,
    "can_help": 3.0,
    "domain": 2.0,
    "profile_summary": 1.0,
}
RULE_SCORE_WEIGHT = 0.35


def retrieve_bm25_rule_candidates(
    gap_context: dict[str, Any],
    mentors: list[dict[str, Any]],
    *,
    search_query: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not gap_context or not mentors or limit <= 0:
        return []

    query = search_query or build_gap_query(gap_context)
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    documents = [_mentor_to_bm25_document(mentor) for mentor in mentors]
    tokenized_documents = [tokenize(document) for document in documents]
    bm25_scores = score_bm25(query_tokens, tokenized_documents)
    gap_terms = set(query_tokens)

    scored_candidates = []
    for index, mentor in enumerate(mentors):
        rule_score, matched_keywords, matched_fields = score_rule_matches(
            mentor,
            gap_terms,
        )
        total_score = bm25_scores[index] + (rule_score * RULE_SCORE_WEIGHT)
        if total_score <= 0:
            continue

        scored_candidates.append(
            (
                -total_score,
                index,
                {
                    **mentor,
                    "retrieval_score": round(total_score, 4),
                    "matched_keywords": matched_keywords,
                    "matched_fields": matched_fields,
                    "retrieval_source": "bm25_rule",
                },
            )
        )

    scored_candidates.sort(key=lambda item: (item[0], item[1]))
    return [candidate for _, _, candidate in scored_candidates[:limit]]


def build_gap_query(gap_context: dict[str, Any]) -> str:
    values = [
        *gap_context.get("query_hints", []),
        *gap_context.get("needed_mentor_expertise", []),
        *gap_context.get("gap_categories", []),
        gap_context.get("main_gap", ""),
    ]
    return " ".join(str(value) for value in values if value)


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw_token in TOKEN_PATTERN.findall(text.casefold()):
        for token in _expand_token(raw_token):
            if len(token) >= 2 and token not in STOPWORDS:
                tokens.append(token)
    return tokens


def score_bm25(
    query_tokens: list[str],
    tokenized_documents: list[list[str]],
    *,
    k1: float = K1,
    b: float = B,
) -> list[float]:
    if not tokenized_documents:
        return []

    document_count = len(tokenized_documents)
    document_lengths = [len(tokens) for tokens in tokenized_documents]
    average_length = sum(document_lengths) / document_count if document_count else 0.0
    document_frequencies = _document_frequencies(tokenized_documents)
    query_counts = Counter(query_tokens)

    scores = []
    for tokens, document_length in zip(tokenized_documents, document_lengths):
        term_frequencies = Counter(tokens)
        score = 0.0
        for token, query_count in query_counts.items():
            tf = term_frequencies.get(token, 0)
            if tf == 0:
                continue

            idf = _idf(document_count, document_frequencies.get(token, 0))
            denominator = tf + k1 * (
                1 - b + b * (document_length / average_length)
            )
            score += query_count * idf * ((tf * (k1 + 1)) / denominator)
        scores.append(score)
    return scores


def score_rule_matches(
    mentor: dict[str, Any],
    gap_terms: set[str],
) -> tuple[float, list[str], list[str]]:
    score = 0.0
    matched_keywords: list[str] = []
    matched_fields: list[str] = []

    for field_name in MATCH_FIELDS:
        values = _field_values(mentor, field_name)
        field_matches = _matched_labels(values, gap_terms)
        if not field_matches:
            continue

        matched_fields.append(field_name)
        matched_keywords.extend(field_matches)
        score += FIELD_WEIGHTS[field_name] * len(field_matches)

    return score, _unique(matched_keywords), matched_fields


def _document_frequencies(tokenized_documents: list[list[str]]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    for tokens in tokenized_documents:
        for token in set(tokens):
            frequencies[token] = frequencies.get(token, 0) + 1
    return frequencies


def _idf(document_count: int, document_frequency: int) -> float:
    return math.log(
        1 + ((document_count - document_frequency + 0.5) / (document_frequency + 0.5))
    )


def _matched_labels(values: list[str], gap_terms: set[str]) -> list[str]:
    labels = []
    for value in values:
        value_terms = set(tokenize(value))
        if any(_terms_match(value_term, gap_term) for value_term in value_terms for gap_term in gap_terms):
            labels.append(_normalize(value))
    return labels


def _terms_match(left: str, right: str) -> bool:
    if left == right:
        return True
    if len(left) >= 3 and left in right:
        return True
    return len(right) >= 3 and right in left


def _field_values(mentor: dict[str, Any], field_name: str) -> list[str]:
    value = mentor.get(field_name, [])
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def _mentor_to_bm25_document(mentor: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(mentor.get("name", "")),
            *_field_values(mentor, "domain"),
            *_field_values(mentor, "keywords"),
            *_field_values(mentor, "can_help"),
            *_field_values(mentor, "profile_summary"),
        ]
    )


def _expand_token(token: str) -> list[str]:
    if not token:
        return []
    split_tokens = [part for part in re.split(r"[./-]+", token) if part]
    if len(split_tokens) > 1:
        return [token, *split_tokens]
    return [token]


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


def _unique(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
