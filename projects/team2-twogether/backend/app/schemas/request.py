from pydantic import BaseModel


class RecommendRequest(BaseModel):
    #: uuid. 프론트가 생성/유지하는 세션 식별자(신규 또는 확인 질문 후 동일 세션).
    #: 인메모리 세션 저장의 키. 빈 값이면 1회성 요청으로 처리한다.
    session_id: str = ""
    project_text: str
    tech_stack: list[str] = []
    stage: str = ""
    clarify_answer: str | None = None