from typing import TypedDict, Any


class GraphState(TypedDict, total=False):
    user_input: str
    tech_stack: list[str]
    stage: str
    clarify_answer: str

    parsed_input: dict[str, Any]
    is_input_sufficient: bool
    question: str
    options: list[str]
    clarification_question: str
    clarification_options: list[str]

    gap_context: dict[str, Any] | None

    search_query: str
    retrieved_mentors: list[dict[str, Any]]

    evaluated_mentors: list[dict[str, Any]]
    is_recommendation_confident: bool
    refined_query: str
    retry_count: int

    final_recommendations: list[dict[str, Any]]
    message: str
    # result_builder(노드4) 가 만드는 최종 응답 페이로드(프론트 계약 그대로).
    final_response: dict[str, Any]
