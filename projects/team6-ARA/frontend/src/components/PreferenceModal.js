import React, { useState } from "react";
import styled from "styled-components";
import { mockPreferenceCandidates } from "../mock";
import { Btn, BtnRow, MockNote, MockBadge } from "../styles/common";
import { theme, radius } from "../styles/theme";

// candidates: BE /feedback/analyze 응답 형태 [{ field, original, preferred }]
// 없으면 목데이터 폴백
export default function PreferenceModal({ candidates = [], onDone }) {
    const isReal = candidates.length > 0;
    const list = isReal ? candidates : mockPreferenceCandidates;

    const [actions, setActions] = useState({});

    function setAction(field, action) {
        setActions((p) => ({ ...p, [field]: action }));
    }

    function handleSave() {
        // '앞으로도 적용' 선택된 후보만 추려서 상위로 전달
        const saved = list.filter((c) => actions[c.field] === "save");
        onDone(saved);
    }

    return (
        <Overlay>
            <ModalCard>
                <ModalHeader>
                    <span>★ 선호 저장 확인</span>
                    <ModalSub>승인·저장 직후 · 닫으면 결과 요약</ModalSub>
                </ModalHeader>
                <ModalBody>
                    <ModalDesc>
                        {!isReal && <><MockBadge />&nbsp;</>}
                        이번 수정에서 <b>반복 가능한 패턴</b>을 선호 후보로 감지했어요.
                        앞으로도 적용할 규칙만 선택하세요.{" "}
                        <Muted>(승인 전엔 장기 저장 안 함)</Muted>
                    </ModalDesc>

                    {list.length === 0 && (
                        <EmptyMsg>수정된 항목이 없어 선호 후보가 없어요.</EmptyMsg>
                    )}

                    {list.map((c) => (
                        <CandCard key={c.field}>
                            <CandRule>
                                {isReal
                                    ? `"${c.field}" 필드: ${JSON.stringify(c.original)} → ${JSON.stringify(c.preferred)}`
                                    : c.rule}
                            </CandRule>
                            {!isReal && (
                                <CandBasis>
                                    <span>근거</span>
                                    <span>{c.basis}</span>
                                </CandBasis>
                            )}
                            <BtnRow style={{ marginTop: "10px" }}>
                                <Btn $sm $primary={actions[c.field] === "save"}     $ghost={actions[c.field] !== "save"}     onClick={() => setAction(c.field, "save")}>앞으로도 적용</Btn>
                                <Btn $sm $primary={actions[c.field] === "one_time"} $ghost={actions[c.field] !== "one_time"} onClick={() => setAction(c.field, "one_time")}>이번만</Btn>
                                <Btn $sm $warn={actions[c.field] === "dismiss"}     $ghost={actions[c.field] !== "dismiss"}   onClick={() => setAction(c.field, "dismiss")}>무시</Btn>
                            </BtnRow>
                        </CandCard>
                    ))}

                    <ModalFooter>
                        <Muted>'앞으로도 적용'만 User Preference Store에 저장됩니다</Muted>
                        <Btn $primary onClick={handleSave}>선택 저장 후 닫기</Btn>
                    </ModalFooter>
                    {!isReal && <MockNote>※ 목데이터 폴백 · 항목 수정 시 BE /feedback/analyze 실제 후보 사용</MockNote>}
                </ModalBody>
            </ModalCard>
        </Overlay>
    );
}

// ===== styled =====
const Overlay = styled.div`
    position: fixed;
    inset: 0;
    background: rgba(44,43,39,.35);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    padding: 20px;
`;

const ModalCard = styled.div`
    background: ${theme.panel};
    border: 2.5px solid ${theme.line};
    border-radius: ${radius.card};
    box-shadow: 6px 9px 0 rgba(0,0,0,.13);
    width: 100%;
    max-width: 660px;
    max-height: 90vh;
    overflow-y: auto;
`;

const ModalHeader = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 2px solid ${theme.line};
    font-size: 17px;
    font-weight: 700;
    background: ${theme.panel2};
`;

const ModalSub = styled.span`
    font-size: 12px;
    color: ${theme.ink2};
    font-weight: 400;
`;

const ModalBody = styled.div`
    padding: 18px 20px;
`;

const ModalDesc = styled.p`
    font-size: 13px;
    color: ${theme.ink2};
    margin: 0 0 14px;
`;

const CandCard = styled.div`
    background: #fff;
    border: 2px solid ${theme.line};
    border-radius: 12px 10px 13px 9px;
    padding: 13px 15px;
    margin-bottom: 12px;
    box-shadow: 2px 3px 0 rgba(0,0,0,.07);
`;

const CandRule = styled.div`
    font-size: 15px;
    font-weight: 700;
`;

const CandBasis = styled.div`
    color: ${theme.agent};
    font-size: 12.5px;
    margin-top: 5px;
    display: flex;
    gap: 7px;

    span:first-child { font-weight: 700; }
`;

const ModalFooter = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
    padding-top: 13px;
    border-top: 2px dashed ${theme.hair};
    flex-wrap: wrap;
    gap: 10px;
`;

const Muted = styled.span`
    font-size: 12px;
    color: ${theme.muted};
`;

const EmptyMsg = styled.div`
    text-align: center;
    color: ${theme.muted};
    font-size: 14px;
    padding: 20px 0;
`;
