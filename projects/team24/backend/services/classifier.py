import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 계약 유형별 고위험 키워드 — analyzer.py의 RISK_CRITERIA와 대응되는 법적 위험 표현 목록
RISK_KEYWORDS_BY_TYPE = {
    "근로": [
        # 임금·급여
        "임금 삭감", "급여 미지급", "지급하지 않", "지급 거부",
        "수습기간 무급", "시급 미달",
        # 해고·퇴직
        "즉시 해고", "사전 통지 없이 해고", "위약금", "손해배상 청구",
        # 경업금지·비밀유지
        "경업금지", "퇴직 후 경업", "동종업계 취업 금지",
        "비밀유지 위반 시 손해배상",
        # 초과근무
        "추가 수당 없음", "연장근로 미지급",
    ],
    "전세": [
        # 보증금
        "보증금 반환 거절", "보증금 공제", "보증금 미반환",
        "보증금을 돌려주지", "반환하지 않",
        # 임대인 면책
        "임대인 책임 없음", "하자 책임 없음",
        # 원상복구
        "원상복구 비용 전액", "수리비 전액 부담",
        # 해지 불이익
        "계약 위반 시 보증금 몰수", "보증금 몰취",
    ],
    "외주": [
        # 대금
        "대금 미지급", "지급 거절", "지체상금", "지연배상",
        "검수 불합격 시 미지급",
        # 저작권·산출물
        "저작권 귀속", "산출물 귀속", "모든 권리 양도",
        "2차 저작물 권리",
        # 유지보수
        "무상 유지보수", "무기한 유지보수", "기간 제한 없이",
        # 손해배상 확대
        "계약금 이상 배상", "실손해 초과 배상",
    ],
    "이용약관": [
        # 자동 갱신·결제
        "자동 갱신", "자동으로 연장", "자동 결제",
        # 개인정보
        "개인정보 제3자 제공", "개인정보 판매", "동의 없이 제공",
        # 일방적 변경
        "약관 일방 변경", "사전 공지 없이 변경", "서비스 중단 면책",
        # 위약금·환불
        "위약금", "해지 위약금", "환불 불가",
        # 서비스 면책
        "서비스 장애 면책", "데이터 손실 면책",
    ],
    "기타": [
        "자동 갱신", "위약금", "일방적 해지",
        "책임 제한", "개인정보 제공", "환불 불가",
    ],
    "매매": [
        # 하자·반품
        "하자 책임 없음", "반품 불가", "환불 거절", "교환 불가",
        # 소유권·이전
        "소유권 이전 지연", "소유권 유보", "인도 거절",
        # 손해배상
        "하자담보 면제", "품질 보증 없음", "AS 불가",
    ],
    "금전소비대차": [
        # 이자·연체
        "이자율 미명시", "연체이자 과다", "복리 적용",
        # 기한·담보
        "기한이익 상실", "담보 강제처분", "즉시 변제",
        # 보증
        "연대보증", "무한책임 보증",
    ],
    "도급": [
        # 대금
        "공사대금 미지급", "설계변경 비용 전가", "추가공사 무상",
        # 하자보수
        "하자보수 무한책임", "하자보수 비용 전액 부담",
        # 지체
        "지체상금 과다", "공기 연장 불인정",
    ],
    "가맹": [
        # 계약 해지
        "가맹비 환불 불가", "일방적 계약 해지", "위약금 과다",
        # 영업
        "영업구역 미보장", "영업시간 강제", "판매가격 강제",
        # 물품
        "필수 물품 강제 구매", "납품 단가 일방 변경",
    ],
}

# 모든 계약 유형에 공통으로 적용되는 극단적 면책·포기 표현
COMMON_HIGH_RISK_KEYWORDS = [
    # 면책·책임 배제
    "면책", "책임지지 않", "책임을 지지", "배상하지 않", "배상 책임 없",
    "손해배상 없음", "손해를 배상하지",
    # 일방적 권리
    "일방적으로", "사전 통보 없이", "사전 동의 없이",
    # 청구 불가
    "청구 불가", "청구할 수 없", "청구권 포기",
    # 해지 강경
    "해지 불가", "해지할 수 없", "취소 불가",
    # 포기·무효 (구체적 표현으로 한정)
    "권리 포기", "청구권을 포기", "계약을 무효", "당연히 무효",
    # 무제한
    "제한 없이", "제한 없는",
]

# 계약 유형별 HIGH 위험 판단 기준 — LLM 폴백 프롬프트에 주입
_HIGH_RISK_CRITERIA = {
    "근로": "임금·수당 미지급, 부당해고·즉시 해고, 과도한 위약금·경업금지, 강행법규(근로기준법) 위반 소지",
    "전세": "보증금 반환 거절·몰수, 임대인 하자 책임 전면 배제, 세입자 계약 해지권 박탈",
    "외주": "대금 지급 완전 거절, 저작권·산출물 전면 귀속, 무기한 무상 유지보수 강제",
    "이용약관": "숨겨진 자동결제·자동갱신, 개인정보 무단 제3자 제공, 사전 공지 없는 일방적 서비스 변경·중단",
    "매매": "하자담보책임 전면 배제, 반품·환불 완전 불가, 소유권 이전 일방적 거절",
    "금전소비대차": "과도한 연체이자·복리, 기한이익 상실 남용, 담보 강제처분·연대보증 무한책임",
    "도급": "공사대금 지급 거절·무기한 지연, 설계변경 비용 수급인 전가, 하자보수 무한·무기한 책임",
    "가맹": "가맹비 환불 완전 불가, 일방적 계약 해지권 남용, 영업구역·가격 강제로 자율성 완전 박탈",
    "기타": "손해배상 청구권 박탈, 계약 해지권 박탈, 일방적 의무 부과",
}

# 부정 수식어: 키워드 매칭 후 바로 뒤에 이 표현이 오면 고위험에서 제외
_NEGATION_SUFFIXES = ("없습니다", "없음", "없다", "않는다", "않음", "않습니다", "아니다", "아닙니다")


def _get_keywords(contract_type: str) -> list[str]:
    """공통 키워드 + 계약 유형별 키워드를 합쳐서 반환한다."""
    type_kw = RISK_KEYWORDS_BY_TYPE.get(contract_type, RISK_KEYWORDS_BY_TYPE["기타"])
    return COMMON_HIGH_RISK_KEYWORDS + type_kw


def _has_keyword_without_negation(text: str, keyword: str) -> bool:
    """텍스트에 키워드가 포함되어 있고, 키워드 직후 15자 이내에 부정 표현이 없으면 True를 반환한다."""
    text = str(text or "")
    idx = text.find(keyword)
    if idx == -1:
        return False
    after = text[idx + len(keyword):idx + len(keyword) + 15]
    return not any(neg in after for neg in _NEGATION_SUFFIXES)


def _llm_classify_risk_level(item: dict, contract_type: str) -> str:
    """키워드로 판별 불가한 위험 조항을 LLM으로 high/medium 분류한다. 오류 시 medium 반환."""
    llm = ChatOpenAI(
        model="solar-pro",
        temperature=0,
        api_key=os.getenv("UPSTAGE_API_KEY"),
        base_url="https://api.upstage.ai/v1",
    )
    high_criteria = _HIGH_RISK_CRITERIA.get(contract_type, _HIGH_RISK_CRITERIA["기타"])
    prompt = PromptTemplate(
        input_variables=["contract_type", "clause", "reason", "high_criteria"],
        template=(
            "당신은 계약서 위험 조항을 전문적으로 분석하는 법률 AI 어시스턴트입니다.\n\n"
            "아래 조항은 1차 분석에서 이미 '위험하다'고 판정된 {contract_type} 계약서의 조항입니다.\n"
            "이제 이 조항의 위험 등급(HIGH / MEDIUM)을 판정하세요.\n\n"
            "[계약 유형] {contract_type}\n"
            "[조항 원문]\n{clause}\n\n"
            "[1차 분석 이유]\n{reason}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "【HIGH 위험 — 즉각 확인 필요】\n"
            "다음 중 하나라도 해당하면 HIGH입니다:\n"
            "① 계약자의 기본 권리(이의 제기, 손해배상 청구, 계약 해지)를 명시적으로 금지·박탈\n"
            "② 일방 당사자에게 무제한적 의무·책임을 강제\n"
            "③ 강행법규(근로기준법, 소비자보호법 등) 위반 소지\n"
            "④ {contract_type} 계약의 핵심 위험 요소: {high_criteria}\n\n"
            "【MEDIUM 위험 — 검토 권장】\n"
            "다음에 해당하면 MEDIUM입니다:\n"
            "① 불리하지만 협상·수정 가능한 조항\n"
            "② 특정 상황에서만 문제가 될 수 있는 조항\n"
            "③ 명확성 부족으로 해석에 따라 불리해질 수 있는 조항\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "다음 순서로 판단하세요:\n"
            "1. 이 조항이 계약 약자의 권리를 어느 정도로 제한하는가?\n"
            "2. 법적 구제 수단(이의 제기, 손해배상 청구)이 차단되어 있는가?\n"
            "3. 일방적·강제적 성격인가, 아니면 협상 여지가 있는가?\n\n"
            "판정 결과를 다음 중 하나로만 답하세요 (다른 말 없이 정확히):\n"
            "HIGH / MEDIUM"
        ),
    )
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({
            "contract_type": contract_type,
            "clause": item.get("clause", ""),
            "reason": item.get("reason", ""),
            "high_criteria": high_criteria,
        }).strip().upper()
        return "high" if "HIGH" in result else "medium"
    except Exception:
        return "medium"


def _is_high_risk(item: dict, keywords: list[str]) -> bool:
    """reason 문장과 clause 원문 양쪽에서 고위험 키워드를 탐색한다. 부정 문맥은 제외한다."""
    targets = [item.get("reason", ""), item.get("clause", "")]
    return any(
        _has_keyword_without_negation(target, kw)
        for kw in keywords
        for target in targets
    )


def classify_risk(analysis: list[dict], contract_type: str = "기타") -> list[dict]:
    """
    LLM 분석 결과에 위험도(risk_level)를 추가한다.

    - low:         is_risky=False
    - high:        is_risky=True + 고위험 키워드 발견 (빠름, 비용 없음)
    - high/medium: is_risky=True + 키워드 미발견 → LLM 폴백으로 판별
    """
    keywords = _get_keywords(contract_type)
    results = []
    if not isinstance(analysis, list):
        return results

    for item in analysis:
        if not isinstance(item, dict):
            continue

        normalized_item = {
            **item,
            "clause": str(item.get("clause") or "").strip(),
            "is_risky": item.get("is_risky") is True,
            "reason": str(item.get("reason") or "분석 이유가 제공되지 않았습니다.").strip(),
        }
        if not normalized_item["is_risky"]:
            risk_level = "low"
        elif _is_high_risk(normalized_item, keywords):
            risk_level = "high"
        else:
            risk_level = _llm_classify_risk_level(normalized_item, contract_type)
        results.append({**normalized_item, "risk_level": risk_level})
    return results
