from pydantic import BaseModel, field_validator


class Participant(BaseModel):
    name: str
    role: str


class AnalyzeRequest(BaseModel):
    text: str
    participants: list[Participant]
    communicationType: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_too_short(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("분석할 텍스트와 필수 소통 정보를 입력해주세요.")
        return v.strip()

    @field_validator("participants")
    @classmethod
    def participants_must_have_at_least_two(cls, v: list[Participant]) -> list[Participant]:
        if len(v) < 2:
            raise ValueError("참여자는 발화자와 수신자를 포함하여 최소 2명이어야 합니다.")
        return v
