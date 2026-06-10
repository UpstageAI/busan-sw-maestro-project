"""되묻기 무한루프 방지 회귀 테스트 (코드리뷰 H1/H2).

직전 턴이 실제 '되묻기'였으면(prev_was_clarification=True),
되묻기 문구가 무엇으로 끝나든(이모지/마침표 등) 클러리파이어는
LLM 호출 없이 곧장 스킵해야 한다. (과거엔 '?'로 끝나는지로만 판단해 실패)
"""
from app.agents.clarifier import check_and_clarify


def test_직전_되묻기_턴이면_재되묻기를_스킵한다():
    state = {
        "query": "음 잘 모르겠어",
        "history_text": "사용자: 그거 어떻게 만들어?\n가이드: 어떤 걸 만들고 싶으신가요? 알려주세요 🌟",
        "prev_was_clarification": True,
    }
    out = check_and_clarify(state)
    assert out["need_clarification"] is False
    assert out["clarification_question"] == ""
