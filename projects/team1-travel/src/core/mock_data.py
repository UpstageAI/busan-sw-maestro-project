"""규칙 기반 국내 관광지 50선 Mock 데이터.

구조 A 의 검색(retrieve) 단계에서 외부 API 없이 동작 검증을 위해 사용한다.
각 항목 스키마:
    name        : 관광지 이름
    region      : 광역 지역 (서울 / 부산 / 강원 / 제주 ...)
    type        : 유형 (자연 / 도시 / 역사 / 체험 / 식도락)
    mood        : 분위기 키워드 리스트
    best_for    : 추천 동행자 유형 리스트 (family / couple / friends / solo)
"""

from typing import Dict, List

TOURIST_SPOTS: List[Dict] = [
    {"name": "경복궁", "region": "서울", "type": "역사", "mood": ["전통", "감성"], "best_for": ["family", "couple", "solo"], "cost_level": "low"},
    {"name": "북촌한옥마을", "region": "서울", "type": "역사", "mood": ["전통", "산책"], "best_for": ["couple", "friends"], "cost_level": "low"},
    {"name": "남산서울타워", "region": "서울", "type": "도시", "mood": ["야경", "로맨틱"], "best_for": ["couple"], "cost_level": "mid"},
    {"name": "홍대거리", "region": "서울", "type": "도시", "mood": ["활기", "젊음"], "best_for": ["friends"], "cost_level": "low"},
    {"name": "롯데월드", "region": "서울", "type": "체험", "mood": ["신남", "활기"], "best_for": ["family", "friends", "couple"], "cost_level": "high"},
    {"name": "한강공원", "region": "서울", "type": "자연", "mood": ["여유", "산책"], "best_for": ["family", "couple", "solo"], "cost_level": "low"},
    {"name": "해운대해수욕장", "region": "부산", "type": "자연", "mood": ["바다", "활기"], "best_for": ["family", "friends", "couple"], "cost_level": "low"},
    {"name": "광안리해변", "region": "부산", "type": "자연", "mood": ["야경", "바다"], "best_for": ["couple", "friends"], "cost_level": "low"},
    {"name": "감천문화마을", "region": "부산", "type": "체험", "mood": ["감성", "사진"], "best_for": ["friends", "couple", "solo"], "cost_level": "low"},
    {"name": "태종대", "region": "부산", "type": "자연", "mood": ["절경", "산책"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "자갈치시장", "region": "부산", "type": "식도락", "mood": ["활기", "먹방"], "best_for": ["friends", "family"], "cost_level": "mid"},
    {"name": "감포해변", "region": "경북", "type": "자연", "mood": ["조용", "바다"], "best_for": ["solo", "couple"], "cost_level": "low"},
    {"name": "경주불국사", "region": "경북", "type": "역사", "mood": ["전통", "사색"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "경주대릉원", "region": "경북", "type": "역사", "mood": ["감성", "산책"], "best_for": ["couple", "family"], "cost_level": "low"},
    {"name": "안동하회마을", "region": "경북", "type": "역사", "mood": ["전통", "고즈넉"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "남이섬", "region": "강원", "type": "자연", "mood": ["힐링", "산책"], "best_for": ["couple", "family"], "cost_level": "mid"},
    {"name": "정동진", "region": "강원", "type": "자연", "mood": ["일출", "감성"], "best_for": ["couple", "solo"], "cost_level": "low"},
    {"name": "강릉안목해변", "region": "강원", "type": "식도락", "mood": ["커피", "바다"], "best_for": ["couple", "solo"], "cost_level": "mid"},
    {"name": "오대산", "region": "강원", "type": "자연", "mood": ["트레킹", "조용"], "best_for": ["solo", "friends"], "cost_level": "low"},
    {"name": "속초중앙시장", "region": "강원", "type": "식도락", "mood": ["먹방", "활기"], "best_for": ["family", "friends"], "cost_level": "mid"},
    {"name": "설악산", "region": "강원", "type": "자연", "mood": ["절경", "트레킹"], "best_for": ["friends", "solo"], "cost_level": "low"},
    {"name": "평창양떼목장", "region": "강원", "type": "체험", "mood": ["힐링", "동물"], "best_for": ["family", "couple"], "cost_level": "mid"},
    {"name": "제주성산일출봉", "region": "제주", "type": "자연", "mood": ["일출", "절경"], "best_for": ["couple", "solo"], "cost_level": "low"},
    {"name": "제주협재해수욕장", "region": "제주", "type": "자연", "mood": ["바다", "에메랄드"], "best_for": ["family", "couple"], "cost_level": "low"},
    {"name": "제주올레길", "region": "제주", "type": "자연", "mood": ["트레킹", "사색"], "best_for": ["solo", "couple"], "cost_level": "low"},
    {"name": "제주카멜리아힐", "region": "제주", "type": "체험", "mood": ["감성", "정원"], "best_for": ["couple", "family"], "cost_level": "mid"},
    {"name": "우도", "region": "제주", "type": "자연", "mood": ["바다", "여유"], "best_for": ["couple", "friends"], "cost_level": "mid"},
    {"name": "한라산", "region": "제주", "type": "자연", "mood": ["트레킹", "절경"], "best_for": ["friends", "solo"], "cost_level": "low"},
    {"name": "전주한옥마을", "region": "전북", "type": "역사", "mood": ["전통", "먹방"], "best_for": ["family", "couple", "friends"], "cost_level": "low"},
    {"name": "내장산", "region": "전북", "type": "자연", "mood": ["단풍", "트레킹"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "여수밤바다", "region": "전남", "type": "도시", "mood": ["야경", "로맨틱"], "best_for": ["couple", "friends"], "cost_level": "mid"},
    {"name": "순천만국가정원", "region": "전남", "type": "자연", "mood": ["힐링", "정원"], "best_for": ["family", "couple"], "cost_level": "mid"},
    {"name": "보성녹차밭", "region": "전남", "type": "자연", "mood": ["힐링", "사진"], "best_for": ["couple", "solo"], "cost_level": "mid"},
    {"name": "담양죽녹원", "region": "전남", "type": "자연", "mood": ["산책", "사색"], "best_for": ["solo", "couple"], "cost_level": "low"},
    {"name": "대구서문시장", "region": "대구", "type": "식도락", "mood": ["먹방", "활기"], "best_for": ["friends", "family"], "cost_level": "mid"},
    {"name": "팔공산", "region": "대구", "type": "자연", "mood": ["트레킹", "조용"], "best_for": ["solo", "friends"], "cost_level": "low"},
    {"name": "대전한밭수목원", "region": "대전", "type": "자연", "mood": ["산책", "여유"], "best_for": ["family", "couple"], "cost_level": "low"},
    {"name": "공주공산성", "region": "충남", "type": "역사", "mood": ["전통", "산책"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "태안안면도", "region": "충남", "type": "자연", "mood": ["바다", "캠핑"], "best_for": ["family", "friends"], "cost_level": "low"},
    {"name": "단양도담삼봉", "region": "충북", "type": "자연", "mood": ["절경", "사진"], "best_for": ["couple", "family"], "cost_level": "low"},
    {"name": "청남대", "region": "충북", "type": "역사", "mood": ["산책", "여유"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "인천차이나타운", "region": "인천", "type": "체험", "mood": ["먹방", "이국적"], "best_for": ["friends", "family"], "cost_level": "mid"},
    {"name": "강화도", "region": "인천", "type": "역사", "mood": ["조용", "사색"], "best_for": ["solo", "couple"], "cost_level": "low"},
    {"name": "월미도", "region": "인천", "type": "체험", "mood": ["활기", "바다"], "best_for": ["friends", "family"], "cost_level": "mid"},
    {"name": "광주국립아시아문화전당", "region": "광주", "type": "도시", "mood": ["문화", "감성"], "best_for": ["solo", "couple"], "cost_level": "low"},
    {"name": "통영동피랑마을", "region": "경남", "type": "체험", "mood": ["감성", "사진"], "best_for": ["couple", "friends"], "cost_level": "low"},
    {"name": "거제외도보타니아", "region": "경남", "type": "자연", "mood": ["정원", "바다"], "best_for": ["couple", "family"], "cost_level": "mid"},
    {"name": "남해독일마을", "region": "경남", "type": "체험", "mood": ["이국적", "감성"], "best_for": ["couple", "friends"], "cost_level": "low"},
    {"name": "진주촉석루", "region": "경남", "type": "역사", "mood": ["전통", "야경"], "best_for": ["family", "solo"], "cost_level": "low"},
    {"name": "울릉도", "region": "경북", "type": "자연", "mood": ["절경", "바다"], "best_for": ["friends", "solo"], "cost_level": "high"},
]

# 50선 데이터 무결성 검증 (import 시점 자체 점검)
assert len(TOURIST_SPOTS) == 50, f"관광지 데이터는 50선이어야 합니다 (현재 {len(TOURIST_SPOTS)})"
