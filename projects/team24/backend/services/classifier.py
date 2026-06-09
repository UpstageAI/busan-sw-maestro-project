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

    - low:    is_risky=False
    - high:   is_risky=True + 고위험 키워드 발견 (reason 또는 clause 원문)
    - medium: is_risky=True + 고위험 키워드 미발견
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
            risk_level = "medium"
        results.append({**normalized_item, "risk_level": risk_level})
    return results
