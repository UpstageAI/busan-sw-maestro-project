import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def explain(clause: str) -> str:
    normalized_clause = str(clause or "").strip()
    fallback = _build_fallback_explanation(normalized_clause)
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        return fallback

    llm = ChatOpenAI(
        model="solar-pro",
        temperature=0,
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
    )
    prompt = PromptTemplate(
        input_variables=["clause"],
        template=(
            "당신은 법률 전문가입니다. 아래 계약서 조항을 일반인이 이해할 수 있도록 설명해주세요.\n\n"
            "조항: {clause}\n\n"
            "다음 항목을 순서대로 답하세요:\n"
            "1. 이 조항의 의미: (2~3문장)\n"
            "2. 계약자에게 불리한 점: (있으면 구체적으로, 없으면 '없음')\n"
            "3. 주의해야 할 점: (실용적인 조언 1~2가지)"
        ),
    )
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"clause": normalized_clause[:3000]}).strip()
        return result or fallback
    except Exception:
        return fallback


def _build_fallback_explanation(clause: str) -> str:
    if not clause:
        return "설명할 조항 내용이 없습니다."
    return (
        "1. 이 조항의 의미: 계약 당사자의 권리와 의무를 정한 조항입니다. "
        "현재 상세 AI 설명을 사용할 수 없어 원문 중심으로 확인이 필요합니다.\n"
        "2. 계약자에게 불리한 점: 자동 판단이 어려우므로 금액, 기간, 해지, "
        "손해배상 및 면책 조건을 확인해 주세요.\n"
        "3. 주의해야 할 점: 불명확하거나 일방적인 표현이 있다면 계약 전에 "
        "상대방과 문구를 조정하고 필요 시 전문가 검토를 받으세요."
    )
