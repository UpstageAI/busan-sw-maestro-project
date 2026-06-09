"""지연시간/정확도 평가용 쿼리 20선.

구조 A 워크플로우의 회귀 테스트 및 성능(지연시간) 측정에 사용한다.
각 쿼리는 (자연어 입력, 기대 의도 일부) 형태로 정의한다.
"""

import time

from src.agents.structure_a import build_graph

# (입력 쿼리, 기대 participant_type) — 정확도 평가용 라벨
EVAL_QUERIES = [
    ("혼자 조용히 사색하기 좋은 산 추천해줘", "solo"),
    ("여자친구랑 2박 3일 바다 여행 가고 싶어", "couple"),
    ("친구들이랑 활기찬 도시 여행 어디가 좋아?", "friends"),
    ("부모님 모시고 갈 만한 전통 명소 알려줘", "family"),
    ("당일치기로 서울 근교 다녀오고 싶어", "solo"),
    ("제주도 커플 여행 코스 추천", "couple"),
    ("아이랑 갈 만한 체험 관광지", "family"),
    ("혼자 떠나는 강릉 카페 투어", "solo"),
    ("친구 4명이서 부산 먹방 여행", "friends"),
    ("예산 적게 드는 힐링 여행지", "solo"),
    ("단풍 보러 가기 좋은 곳", "solo"),
    ("야경 예쁜 데이트 장소", "couple"),
    ("가족과 함께하는 자연 휴양지", "family"),
    ("이국적인 분위기의 국내 여행지", "couple"),
    ("일출 보기 좋은 곳 추천", "couple"),
    ("전주 한옥마을 같은 전통 여행지", "family"),
    ("친구들과 캠핑하기 좋은 바다", "friends"),
    ("혼자 트레킹하기 좋은 산", "solo"),
    ("3박 4일 제주 한 바퀴", "couple"),
    ("오늘 점심 메뉴 추천해줘", "solo"),  # reject 케이스
]


def test_all_queries_run():
    """모든 평가 쿼리가 예외 없이 응답을 생성하는지 + 지연시간 측정."""
    app = build_graph()
    latencies = []
    for query, _expected in EVAL_QUERIES:
        start = time.perf_counter()
        result = app.invoke({"user_query": query})
        latencies.append(time.perf_counter() - start)
        assert result.get("response"), f"빈 응답: {query}"

    avg = sum(latencies) / len(latencies)
    print(f"\n총 {len(EVAL_QUERIES)}개 쿼리 평균 지연시간: {avg * 1000:.1f} ms")


if __name__ == "__main__":
    test_all_queries_run()
    print("✅ 평가 쿼리 20선 통과")
