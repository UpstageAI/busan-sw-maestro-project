"""OpenWeather 5일 예보 API 래퍼."""

from __future__ import annotations

import requests

from src.config import OPENWEATHER_API_KEY
from src.tools.region_coords import REGION_COORDS


def get_weather(lat: float, lon: float, target_date: str | None = None) -> dict | None:
    """OpenWeather 예보에서 (lat, lon) 위치의 날씨 정보를 반환한다."""
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric", "lang": "kr"},
            timeout=5,
        )
        items = resp.json().get("list", [])
        if not items:
            return None
        entry = items[0]
        if target_date:
            for item in items:
                if item.get("dt_txt", "").startswith(f"{target_date} 12:"):
                    entry = item
                    break
        weather = entry.get("weather", [{}])[0]
        rain = entry.get("pop", 0.0)
        return {
            "description": weather.get("description", ""),
            "temp": float(entry.get("main", {}).get("temp", 0.0)),
            "rain_prob": float(rain),
        }
    except Exception:
        return None


def get_region_weather(region: str, target_date: str | None = None) -> dict | None:
    """REGION_COORDS에서 지역 좌표를 조회해 날씨 정보를 반환한다."""
    coords = REGION_COORDS.get(region)
    if coords is None:
        return None
    return get_weather(coords[0], coords[1], target_date)
