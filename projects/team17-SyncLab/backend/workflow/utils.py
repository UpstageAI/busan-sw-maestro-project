import json


def call_llm_with_json_retry(llm, prompt: str, max_retries: int = 2) -> dict:
    """
    LLM을 호출하고 JSON 파싱에 실패하면
    잘못된 응답을 피드백으로 보내 재시도한다.
    """
    response = llm.invoke(prompt)
    content = response.content.strip()

    for attempt in range(max_retries + 1):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            if attempt == max_retries:
                raise ValueError(
                    f"LLM이 {max_retries + 1}번 시도 후에도 유효한 JSON을 반환하지 않았습니다.\n"
                    f"마지막 응답:\n{content[:400]}"
                )

            feedback = (
                f"방금 반환한 응답이 유효한 JSON이 아닙니다.\n"
                f"마크다운 코드블록(```json ... ```)이나 설명 텍스트 없이 "
                f"순수 JSON만 다시 반환하세요.\n\n"
                f"잘못된 응답:\n{content}\n\n"
                f"위 내용을 올바른 JSON 형식으로 수정해서 반환하세요."
            )
            response = llm.invoke(feedback)
            content = response.content.strip()

    raise ValueError("JSON 파싱 실패")
