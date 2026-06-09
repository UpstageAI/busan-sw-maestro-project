"""가드레일 회귀 테스트.

분류 자체는 LLM 기반이라 결정론 단위테스트가 어렵다(프롬프트 강화 + 실제 호출로 검증).
여기서는 LLM 없이 결정적인 부분 — out_of_scope로 분류된 질문이 일반 LLM 답변 대신
'마크 질문 권유' 고정 문구로 거절되는지 — 를 고정한다.
"""
from app.agents.responder import generate_answer
from app.prompts.templates import OUT_OF_SCOPE_RESPONSE


def test_out_of_scope는_고정_거절문구를_반환한다():
    out = generate_answer({"domain": "out_of_scope", "query": "제철과일 뭐야?"})
    assert out["final_answer"] == OUT_OF_SCOPE_RESPONSE


def test_거절문구는_마크_질문을_권한다():
    assert "마인크래프트" in OUT_OF_SCOPE_RESPONSE
