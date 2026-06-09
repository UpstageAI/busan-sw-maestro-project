"""환경변수 로드 및 LangSmith 관측성 세팅 연결.

`.env` 파일(.env.template 복사본)을 읽어 Upstage / LangSmith 키를 로드하고,
LangSmith 추적에 필요한 환경변수를 프로세스 환경에 주입한다.
"""

import os

from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
load_dotenv()

# --- Upstage Solar ---
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

# --- Kakao Local ---
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

# --- OpenWeather ---
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- LangSmith 관측성(Observability) ---
LANGSMITH_TRACING_V2 = os.getenv("LANGSMITH_TRACING_V2", "false")
LANGSMITH_ENDPOINT = os.getenv(
    "LANGSMITH_ENDPOINT", "https://api.smith.langchain.com/"
)
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "travel-agentic-workflow")


def setup_langsmith() -> None:
    """LangSmith 추적용 환경변수를 LangChain 이 인식하는 키로 주입한다."""
    os.environ["LANGCHAIN_TRACING_V2"] = LANGSMITH_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
    if LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT


def validate_keys() -> None:
    """필수 키 누락 시 빠르게 실패시켜 디버깅을 돕는다."""
    if not UPSTAGE_API_KEY:
        raise EnvironmentError(
            "UPSTAGE_API_KEY 가 설정되지 않았습니다. "
            ".env.template 을 복사해 .env 를 만들고 키를 입력하세요."
        )
