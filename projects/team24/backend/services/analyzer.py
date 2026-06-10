import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

VALID_TYPES = ["근로", "전세", "외주", "이용약관", "기타"]

RISK_CRITERIA = {
    "근로": "임금/급여 지급 조건, 근로시간, 수습기간, 퇴사·해지 조건, 위약금, 비밀유지·경업금지",
    "전세": "보증금 반환 조건, 특약사항, 계약 해지, 원상복구 범위, 임대인 책임",
    "외주": "대금 지급 시점·조건, 지체상금/지연배상, 저작권·산출물 귀속, 유지보수 범위",
    "이용약관": "자동 갱신, 과도한 위약금, 개인정보 제3자 제공, 책임 제한·면책, 일방적 해지",
    "기타": "자동 갱신, 과도한 위약금, 일방적 해지, 책임 제한, 개인정보 제공",
}

CONTRACT_TYPE_KEYWORDS = {
    "근로": ("근로자", "사용자", "임금", "급여", "퇴직", "근로시간"),
    "전세": ("전세", "임대인", "임차인", "보증금", "임대차"),
    "외주": ("용역", "외주", "산출물", "검수", "발주", "대금"),
    "이용약관": ("이용약관", "회원", "이용자", "서비스", "개인정보"),
}

FALLBACK_RISK_KEYWORDS = (
    "위약금",
    "면책",
    "책임지지 않",
    "청구하지 않",
    "청구할 수 없",
    "반환하지 않",
    "환불 불가",
    "자동 갱신",
    "일방적",
    "동의 없이",
    "무상 유지보수",
    "경업금지",
    "개인정보 제3자 제공",
    "지급 거절",
    "미지급",
    "권리 포기",
    "제한 없이",
)


def detect_contract_type(text: str) -> str:
    fallback_type = _detect_contract_type_by_keywords(text)
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        return fallback_type

    llm = ChatOpenAI(
        model="solar-pro",
        temperature=0,
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
    )
    prompt = PromptTemplate(
        input_variables=["text"],
        template=(
            "아래 계약서 내용을 읽고 계약 유형을 판단하세요.\n\n"
            "{text}\n\n"
            "다음 중 하나로만 답하세요 (다른 말 없이 정확히 한 단어):\n"
            "근로 / 전세 / 외주 / 이용약관 / 기타"
        ),
    )
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"text": text[:2000]}).strip()
    except Exception:
        return fallback_type

    normalized = next(
        (contract_type for contract_type in VALID_TYPES if contract_type in result),
        None,
    )
    return normalized or fallback_type


def analyze_clauses(clauses: list[str], contract_type: str) -> list[dict]:
    if not isinstance(clauses, list):
        return []

    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        return [_analyze_clause_by_rules(clause) for clause in clauses]

    llm = ChatOpenAI(
        model="solar-pro",
        temperature=0,
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
    )
    criteria = RISK_CRITERIA.get(contract_type, RISK_CRITERIA["기타"])
    prompt = PromptTemplate(
        input_variables=["contract_type", "criteria", "clause"],
        template=(
            "당신은 법률 전문가입니다. 아래는 {contract_type} 계약서의 조항입니다.\n"
            "이 조항이 계약자에게 불리하거나 위험한지 판단하세요.\n\n"
            "다음 항목들을 특히 중점적으로 점검하세요: {criteria}\n\n"
            "조항: {clause}\n\n"
            "다음 형식으로만 답하세요:\n"
            "위험여부: (예/아니오)\n"
            "이유: (한 문장으로)"
        ),
    )
    chain = prompt | llm | StrOutputParser()
    results = []

    for clause in clauses:
        normalized_clause = str(clause).strip()
        try:
            text_out = chain.invoke(
                {
                    "contract_type": contract_type,
                    "criteria": criteria,
                    "clause": normalized_clause[:3000],
                }
            ).strip()
            results.append(_parse_analysis_response(normalized_clause, text_out))
        except Exception:
            results.append(_analyze_clause_by_rules(normalized_clause))

    return results


def _detect_contract_type_by_keywords(text: str) -> str:
    normalized_text = str(text or "")
    scores = {
        contract_type: sum(
            normalized_text.count(keyword) for keyword in keywords
        )
        for contract_type, keywords in CONTRACT_TYPE_KEYWORDS.items()
    }
    detected_type, score = max(scores.items(), key=lambda item: item[1])
    return detected_type if score else "기타"


def _parse_analysis_response(clause: str, response: str) -> dict:
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    risk_match = re.search(
        r"위험\s*여부\s*:\s*(예|아니오)",
        response,
    )
    if risk_match:
        is_risky = risk_match.group(1) == "예"
    else:
        first_line = lines[0] if lines else ""
        is_risky = first_line.strip().startswith("예")

    reason_match = re.search(r"이유\s*:\s*(.+)", response)
    reason = reason_match.group(1).strip() if reason_match else ""
    if not reason:
        reason = (
            "계약자에게 불리할 수 있는 조건이 확인되었습니다."
            if is_risky
            else "특별한 위험 요소가 확인되지 않았습니다."
        )

    return {"clause": clause, "is_risky": is_risky, "reason": reason}


def _analyze_clause_by_rules(clause: str) -> dict:
    normalized_clause = str(clause or "").strip()
    matched_keywords = [
        keyword for keyword in FALLBACK_RISK_KEYWORDS if keyword in normalized_clause
    ]
    is_risky = bool(matched_keywords)
    reason = (
        f"주의가 필요한 표현({', '.join(matched_keywords[:3])})이 포함되어 있습니다."
        if is_risky
        else "규칙 기반 점검에서 뚜렷한 위험 표현이 확인되지 않았습니다."
    )
    return {
        "clause": normalized_clause,
        "is_risky": is_risky,
        "reason": reason,
    }
