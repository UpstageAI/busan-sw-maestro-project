from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from ..config import get_settings


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    s = get_settings()
    return OpenAI(api_key=s.upstage_api_key, base_url=s.upstage_base_url)


def chat(messages: list[dict], temperature: float = 0.3, json_mode: bool = False) -> str:
    """공용 LLM 호출 헬퍼. 응답 텍스트를 반환한다."""
    s = get_settings()
    kwargs: dict = {"model": s.chat_model, "messages": messages, "temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = get_client().chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def embed_query(text: str) -> list[float]:
    """쿼리 임베딩. Upstage query 모델 사용."""
    s = get_settings()
    response = get_client().embeddings.create(model=s.embedding_model, input=text)
    return response.data[0].embedding
