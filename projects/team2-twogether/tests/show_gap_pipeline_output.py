import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from backend.app.nodes.interview_gap import analyze_project_gap


MOCK_PARSED_INPUT = {
    "project_summary": "SW마에스트로 멘토 추천 Agentic RAG 서비스",
    "tech_stack": ["FastAPI", "LangGraph", "Upstage", "RAG", "Streamlit"],
    "current_stage": "초기 구현 단계",
    "concerns": ["RAG 검색 품질", "추천 근거 생성", "LangGraph 분기 설계"],
    "domain": ["AI", "Agent", "Recommendation"],
    "constraints": ["짧은 개발 기간", "로컬 데모 중심", "합성 멘토 데이터 사용"],
    "user_goal": "현재 프로젝트의 부족한 역량을 보완해줄 멘토 추천",
}


def main() -> None:
    gap_context = analyze_project_gap(MOCK_PARSED_INPUT)
    print("parsed_input")
    print(json.dumps(MOCK_PARSED_INPUT, ensure_ascii=False, indent=2))
    print("\ngap_context")
    print(json.dumps(gap_context.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
