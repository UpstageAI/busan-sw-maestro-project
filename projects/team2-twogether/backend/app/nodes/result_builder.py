"""Result Builder Node (워크플로우 4) — 최종 추천 결과 카드 생성.

LangGraph 워크플로우의 마지막 노드. 적합도 평가 노드(fit_evaluation)가 만든
``evaluated_mentors``(점수 내림차순 정렬)와 약점 분석(``gap_context``)을 받아,
프론트엔드 계약(`frontend/src/types/api.ts` 의 ``RecommendResponse``)에 맞는
최종 응답 페이로드를 만든다.

설계 기준:
- 상위 N명(기본 3)만 카드로 노출 (화면 명세 S-04: "상위 2~3명").
- ``is_recommendation_confident`` 로 ``recommended`` / ``limited`` 결정.
  (fit_evaluation 이 max score >= 60 기준으로 이미 계산해 둠)
- 환각 방지: ``reason`` 은 fit_evaluation 이 멘토/약점 데이터로 생성한 텍스트를
  **그대로 통과**시키며 여기서 새 사실을 만들지 않는다. ``notice`` 도 실제
  ``gap_context`` 값만 끼워 넣는다.
- 내부 전용 필드(``mentor_id``, ``retrieval_score``, ``matched_keywords``)는
  최종 카드에서 제거한다.
"""

from __future__ import annotations

from typing import Any

from backend.app.nodes.mentor_retrieval import load_mentors

#: 최종 추천 카드 최대 개수 (화면 명세 S-04 "상위 2~3명").
TOP_N = 3


def result_builder_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph 노드 진입점. state 부분 업데이트(dict)를 반환한다.

    - ``final_response``: 프론트로 그대로 직렬화 가능한 응답 페이로드.
    - ``final_recommendations``: 멘토 카드 리스트(기존 GraphState 키 호환).
    - ``message``: limited 안내(notice) 또는 빈 문자열(기존 키 호환).
    """
    response = build_recommendation_response(state)
    return {
        "final_response": response,
        "final_recommendations": response.get("mentors", []),
        "message": response.get("notice", ""),
    }


def build_recommendation_response(state: dict[str, Any]) -> dict[str, Any]:
    """state → 프론트 계약 응답 페이로드(순수 함수, 테스트 대상).

    반환 형태(status 별):
      - recommended: ``{status, gaps, refined, mentors}``
      - limited:     ``{status, gaps, mentors, notice}``
    """
    evaluated_mentors = state.get("evaluated_mentors") or []
    gap_context = state.get("gap_context") or {}
    is_confident = bool(state.get("is_recommendation_confident"))
    refined = int(state.get("retry_count", 0) or 0) > 0

    gaps = _build_gaps(gap_context)
    top_mentors = evaluated_mentors[:TOP_N]
    keyword_lookup = _clean_keyword_lookup()
    mentors = [_to_card(mentor, keyword_lookup) for mentor in top_mentors]

    if is_confident and mentors:
        return {
            "status": "recommended",
            "gaps": gaps,
            "refined": refined,
            "mentors": mentors,
        }

    return {
        "status": "limited",
        "gaps": gaps,
        "mentors": mentors,
        "notice": _build_notice(gap_context, has_mentors=bool(mentors)),
    }


def _build_gaps(gap_context: dict[str, Any]) -> list[str]:
    """프론트 "분석된 약점" 배너에 쓸 키워드. gap_categories 우선, 없으면 main_gap."""
    categories = gap_context.get("gap_categories")
    if isinstance(categories, list) and categories:
        return [str(item) for item in categories if str(item).strip()]

    main_gap = str(gap_context.get("main_gap", "")).strip()
    return [main_gap] if main_gap else []


def _build_notice(gap_context: dict[str, Any], *, has_mentors: bool) -> str:
    """limited 안내 문구. 환각 방지를 위해 gap_context 의 실제 값만 끼워 넣는다."""
    if not has_mentors:
        return "조건에 맞는 멘토를 찾지 못했어요. 입력을 조금 더 구체화해볼까요?"

    main_gap = str(gap_context.get("main_gap", "")).strip()
    base = "정확히 맞는 멘토가 부족해 근거가 제한적입니다."
    if main_gap:
        return f"{base} {main_gap} 인접 영역의 멘토를 함께 제시합니다."
    return base


def _to_card(mentor: dict[str, Any], keyword_lookup: dict[str, list[str]]) -> dict[str, Any]:
    """평가된 멘토(dict) → 프론트 ``Mentor`` 카드. 내부 필드는 버린다."""
    return {
        "name": str(mentor.get("name", "")),
        "domain": _str_list(mentor.get("domain")),
        "keywords": _card_keywords(mentor, keyword_lookup),
        "score": _display_score(mentor.get("score")),
        # 환각 방지: reason 은 fit_evaluation 이 만든 근거를 그대로 노출.
        "reason": str(mentor.get("reason", "")),
        "can_help": _str_list(mentor.get("can_help")),
        "less_relevant_for": _str_list(mentor.get("less_relevant_for")),
        "profile_summary": str(mentor.get("profile_summary", "")),
    }


def _card_keywords(
    mentor: dict[str, Any],
    keyword_lookup: dict[str, list[str]],
) -> list[str]:
    """카드/상세 모달용 깨끗한 키워드.

    우선순위:
      1) 멘토 dict 가 원본 ``keywords`` 를 직접 들고 있으면 사용.
         (노드2 retrieved_mentors 는 keywords 를 포함하므로, 노드3가 이를
         보존하면 이 경로로 바로 해결됨)
      2) 없으면 mentors.json 원본 keywords 를 mentor_id 로 복구.
      3) 그래도 없으면 matched_keywords 폴백(긴 문장형 토큰은 제외).
    """
    own = mentor.get("keywords")
    if isinstance(own, list) and own:
        return _str_list(own)

    mentor_id = str(mentor.get("mentor_id", ""))
    clean = keyword_lookup.get(mentor_id)
    if clean:
        return clean

    matched = mentor.get("matched_keywords")
    if isinstance(matched, list):
        # 한 두 단어짜리 짧은 토큰만 유지(긴 문장형 키워드 제외).
        return _dedupe(
            str(item)
            for item in matched
            if str(item).strip() and len(str(item)) <= 30
        )
    return []


def _clean_keyword_lookup() -> dict[str, list[str]]:
    """mentor_id → 원본 keywords 매핑. mentors.json 로딩 실패 시 빈 dict."""
    lookup: dict[str, list[str]] = {}
    for mentor in load_mentors():
        mentor_id = str(mentor.get("mentor_id", ""))
        if mentor_id:
            lookup[mentor_id] = _str_list(mentor.get("keywords"))
    return lookup


def _display_score(score: Any) -> int:
    """카드 표시용 정수 점수(0~100). 화면은 '적합 92' 형태."""
    try:
        return max(0, min(100, round(float(score))))
    except (TypeError, ValueError):
        return 0


def _str_list(value: Any) -> list[str]:
    """list[str] 로 정규화. 단일 값/None 도 안전 처리."""
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None or str(value).strip() == "":
        return []
    return [str(value)]


def _dedupe(items: Any) -> list[str]:
    """순서 유지 중복 제거."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
