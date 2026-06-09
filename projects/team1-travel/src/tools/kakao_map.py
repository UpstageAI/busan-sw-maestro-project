"""지오코딩(Nominatim), Kakao 맛집 검색, 거리 계산 유틸리티."""

from __future__ import annotations

import math
import re

import requests

from src.config import KAKAO_API_KEY


def geocode(query: str) -> tuple[float, float] | None:
    """OpenStreetMap Nominatim으로 장소명을 (위도, 경도)로 변환한다.

    API 키 불필요. 초당 1요청 제한(rate limit)이 있으나 단일 호출 용도로는 충분.
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{query} 한국", "format": "json", "limit": 1},
            headers={"User-Agent": "travel-agent-demo/1.0"},
            timeout=5,
        )
        results = resp.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 간 직선 거리(km)를 하버사인 공식으로 계산한다."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _kakao_search(query: str, category_group_code: str, k: int) -> list[dict]:
    """Kakao 로컬 키워드 검색 내부 함수."""
    if not KAKAO_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/keyword.json",
            params={"query": query, "category_group_code": category_group_code, "size": k},
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            timeout=5,
        )
        docs = resp.json().get("documents", [])
        return [
            {
                "name": d["place_name"],
                "address": d["address_name"],
                "category": d.get("category_name", "").split(" > ")[-1],
            }
            for d in docs
        ]
    except Exception:
        return []


def search_restaurants(destination: str, region: str = "", k: int = 5) -> list[dict]:
    """Kakao 검색으로 여행지 주변 음식점(FD6)과 카페(CE7)를 반환한다.

    destination 이름으로 먼저 검색하고, 결과가 부족하면 region으로 보완한다.
    """
    restaurants = _kakao_search(f"{destination} 맛집", "FD6", k)
    cafes = _kakao_search(f"{destination} 카페", "CE7", max(k // 2, 2))

    # 결과가 너무 적으면 더 넓은 지역(region)으로 보완
    if region and len(restaurants) < 3:
        restaurants += _kakao_search(f"{region} 맛집", "FD6", k - len(restaurants))
    if region and len(cafes) < 2:
        cafes += _kakao_search(f"{region} 카페", "CE7", 2 - len(cafes))

    # 중복 제거 (name 기준)
    seen: set[str] = set()
    result = []
    for r in restaurants + cafes:
        if r["name"] not in seen:
            seen.add(r["name"])
            result.append(r)
    return result


def parse_radius_km(travel_radius: str | None) -> float | None:
    """travel_radius 문자열을 km 상한값(float)으로 변환한다."""
    if travel_radius is None or travel_radius == "전국":
        return None
    if travel_radius == "근교":
        return 150.0
    if travel_radius == "당일치기":
        return 100.0
    match = re.search(r"(\d+(?:\.\d+)?)", travel_radius)
    if match:
        return float(match.group(1))
    return None
