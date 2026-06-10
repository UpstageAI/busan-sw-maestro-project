from langchain_core.language_models.chat_models import BaseChatModel
from langchain_upstage import ChatUpstage

# 강의 노트북과 동일한 모델명 사용
MODEL = "solar-pro2"


def get_llm(temperature: float = 0.0, model: str | None = None, streaming: bool = False) -> BaseChatModel:
    """Upstage Solar LLM 클라이언트를 생성한다.

    api_key는 환경변수 UPSTAGE_API_KEY에서 자동으로 읽어온다.
    streaming=True 시 astream_events에서 on_chat_model_stream 이벤트가 발생한다.
    """
    return ChatUpstage(model=model or MODEL, temperature=temperature, streaming=streaming)
