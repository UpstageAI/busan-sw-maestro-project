"""app.knowledge.facts.lookup_facts 단위/회귀 테스트.

채굴 티어·레시피 환각(이슈 #7)을 막기 위해, 질문에 해당하는
'확정 사실'이 올바르게 조회되는지 검증한다.
"""
from app.knowledge.facts import lookup_facts


def test_철_채굴_질문에_돌_곡괭이_티어_사실을_반환한다():
    facts = lookup_facts("철은 어떻게 캐?", ["철", "곡괭이"])
    joined = " ".join(facts)
    assert "철광석" in joined
    assert "돌 곡괭이" in joined


def test_가위_질문에_철_주괴_제련_사실까지_반환한다():
    # 양털→가위 경로에서 "돌→철주괴" 날조가 나왔던 회귀 케이스.
    # 가위=철 주괴 2 + 철 주괴=제련 을 함께 주입해야 한다.
    facts = lookup_facts("양털 어떻게 구해?", ["양털", "가위"])
    joined = " ".join(facts)
    assert "가위" in joined
    assert "철 주괴 2" in joined
    assert "제련" in joined


def test_다이아_채굴은_금_곡괭이_제외를_명시한다():
    # 사용자 교정: '철 곡괭이 이상'에 금 곡괭이는 포함되지 않는다.
    facts = lookup_facts("다이아 어떻게 캐?", ["다이아"])
    joined = " ".join(facts)
    assert "다이아몬드 광석" in joined
    assert "금 곡괭이 제외" in joined


def test_관련없는_질문은_빈_리스트를_반환한다():
    # 매칭 사실이 없으면 기존 위키 기반 답변을 유지하도록 빈 리스트.
    assert lookup_facts("안녕 반가워", ["인사"]) == []
