"""구조화 데이터 스키마 정의 (기획서 3.1절 TravelIntent).

설계 원칙:
- 필드명은 snake_case 로 고정한다.
- 필수값(human_count, participant_type, intent_type)은 기본값으로 보장한다.
- 선택값은 Optional + null(None) 허용으로 둔다.
- 리스트형 필드는 default_factory 로 빈 리스트를 할당해 에러를 방지한다.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TravelIntent(BaseModel):
    """자연어 여행 요청에서 추출한 구조화 의도(Intent)."""

    intent_type: str = Field(
        default="travel_recommend",
        description="요청 유형 분류 (travel_recommend / reject)",
    )
    location_preference: Optional[str] = Field(
        default=None, description="선호 지역 또는 목적지"
    )
    origin: Optional[str] = Field(
        default=None, description="출발지 (예: 서울, 부산)"
    )
    origins: List[str] = Field(
        default_factory=list,
        description="복수 출발지 목록. 참여자들이 서로 다른 곳에서 출발할 때 각 출발지를 기입. 단일 출발지면 빈 리스트.",
    )
    travel_radius: Optional[str] = Field(
        default=None, description="이동 반경 (예: 근교, 전국, 100km 이내)"
    )
    transport_mode: Optional[str] = Field(
        default=None, description="이동 수단 (예: 자가용, 대중교통, 기차)"
    )
    duration_nights: Optional[int] = Field(
        default=None, description="숙박 일수 (0 = 당일치기)"
    )
    start_date: Optional[str] = Field(
        default=None, description="출발 희망일 (YYYY-MM-DD)"
    )
    human_count: int = Field(default=1, description="총 인원 수")
    participant_type: str = Field(
        default="solo",
        description="동행자 유형 (family / couple / friends / solo)",
    )
    constraints: List[str] = Field(
        default_factory=list, description="제약 조건 목록"
    )
    mood_keywords: List[str] = Field(
        default_factory=list, description="분위기/무드 키워드"
    )
    budget_level: Optional[str] = Field(
        default=None, description="예산 수준 (low / mid / high)"
    )


class TimelineItem(BaseModel):
    """타임라인 한 단위(일정 항목)."""

    time: str = Field(description="시간 (예: 09:00, 09:00-10:30)")
    place: str = Field(description="장소")
    activity: str = Field(description="활동 (예: 카페 가기, 해변 산책)")
    transport: Optional[str] = Field(
        default=None, description="해당 장소로의 이동 수단"
    )
    cost: Optional[str] = Field(
        default=None, description="예상 비용 (예: 무료, 15,000원)"
    )


class Timeline(BaseModel):
    """최종 출력: 선택 여행지의 상세 타임라인."""

    destination: str = Field(description="추천(선택) 여행지 또는 지역")
    items: List[TimelineItem] = Field(
        default_factory=list, description="시간순 일정 항목 목록"
    )


# --- 노드 간 LLM 구조화 출력용 보조 스키마 ---


class SpotSelection(BaseModel):
    """generate_candidates: 의미 기반으로 선별된 후보 관광지 이름 목록."""

    names: List[str] = Field(
        default_factory=list, description="후보 목록에서 선별한 관광지 이름"
    )


class SpotFitness(BaseModel):
    """후보 1곳의 적합도 평가 결과."""

    name: str = Field(description="관광지 이름")
    score: int = Field(description="적합도 점수 (0~10)")
    reason: str = Field(default="", description="평가 이유 (간단히)")


class FitnessReport(BaseModel):
    """evaluate_fitness: 후보별 적합도 평가 결과."""

    evaluations: List[SpotFitness] = Field(
        default_factory=list, description="후보별 적합도 평가 목록"
    )
