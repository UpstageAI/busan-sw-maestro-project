"""확정 사실(structured_facts)을 프롬프트 블록으로 변환하는 로직 테스트.

LLM 호출 없이 '주입' 부분만 순수 함수로 검증한다.
"""
from app.prompts.templates import format_facts_block


def test_빈_사실은_빈_문자열을_반환한다():
    # 매칭 사실이 없으면 프롬프트를 변형하지 않는다(기존 동작 유지).
    assert format_facts_block([]) == ""


def test_사실_블록은_사실과_위키보다_우선_지침을_포함한다():
    block = format_facts_block(["철광석: 돌 곡괭이 이상 필요 (나무·금 곡괭이로는 못 캠)"])
    assert "철광석: 돌 곡괭이 이상 필요" in block
    assert "우선" in block  # 참고 위키와 충돌 시 이 규칙을 우선하라는 지침
