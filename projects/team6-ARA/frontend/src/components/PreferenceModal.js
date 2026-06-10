import React, { useState } from "react";
import styled from "styled-components";
import { resumeRun } from "../api/analyze";
import { Btn, BtnRow } from "../styles/common";
import { theme, radius } from "../styles/theme";

// candidates: 그래프 2차 interrupt 의 선호 후보 [{ field, original, preferred, pattern_type, log_id }]
// 후보가 없으면(그래프가 바로 완료) 안내 후 건너뛴다. 목데이터는 쓰지 않는다.
export default function PreferenceModal({ sessionId, candidates = [], onDone }) {
    // 후보는 index 로 식별한다(여러 항목이 같은 field 를 수정하면 field 가 중복될 수 있음).
    const [actions, setActions] = useState({});
    const [submitting, setSubmitting] = useState(false);

    function setAction(idx, action) {
        setActions((p) => ({ ...p, [idx]: action }));
    }

    async function handleSave() {
        // 모든 후보를 선택된 action 으로 2차 resume 에 보낸다(미선택은 dismiss).
        const preference_choices = candidates.map((c, i) => ({
            field: c.field,
            action: actions[i] || "dismiss",
            original: c.original,
            preferred: c.preferred,
            log_id: c.log_id,
        }));
        setSubmitting(true);
        try {
            const result = await resumeRun(sessionId, { preference_choices });
            onDone(result);
        } catch (e) {
            // 저장 실패해도 흐름은 진행(데모 안전)
            onDone(null);
        }
    }

    // 선호 후보가 없으면 모달 대신 안내 + 건너뛰기
    if (candidates.length === 0) {
        return (
            <Overlay>
                <ModalCard>
                    <ModalHeader>
                        <span>★ 선호 저장 확인</span>
                    </ModalHeader>
                    <ModalBody>
                        <EmptyMsg>
                            저장할 선호 후보가 없습니다.<br />
                            <Muted>수정한 항목이 없어 학습할 선호 패턴이 없어요.</Muted>
                        </EmptyMsg>
                        <ModalFooter>
                            <span />
                            <Btn $primary onClick={() => onDone(null)}>건너뛰기</Btn>
                        </ModalFooter>
                    </ModalBody>
                </ModalCard>
            </Overlay>
        );
    }

    return (
        <Overlay>
            <ModalCard>
                <ModalHeader>
                    <span>★ 선호 저장 확인</span>
                    <ModalSub>수정 직후 · 닫으면 결과 요약</ModalSub>
                </ModalHeader>
                <ModalBody>
                    <ModalDesc>
                        이번 수정에서 <b>반복 가능한 패턴</b>을 선호 후보로 감지했어요.
                        앞으로도 적용할 규칙만 선택하세요.{" "}
                        <Muted>(승인 전엔 장기 저장 안 함)</Muted>
                    </ModalDesc>

                    {candidates.map((c, i) => (
                        <CandCard key={i}>
                            <CandRule>
                                {`"${c.field}" 필드: ${JSON.stringify(c.original)} → ${JSON.stringify(c.preferred)}`}
                            </CandRule>
                            {c.pattern_type && (
                                <CandBasis>
                                    <span>패턴</span>
                                    <span>{c.pattern_type === "recurring" ? "반복 패턴" : "1회성"}</span>
                                </CandBasis>
                            )}
                            <BtnRow style={{ marginTop: "10px" }}>
                                <Btn $sm $primary={actions[i] === "save"}     $ghost={actions[i] !== "save"}     onClick={() => setAction(i, "save")}>앞으로도 적용</Btn>
                                <Btn $sm $primary={actions[i] === "one_time"} $ghost={actions[i] !== "one_time"} onClick={() => setAction(i, "one_time")}>이번만</Btn>
                                <Btn $sm $warn={actions[i] === "dismiss"}     $ghost={actions[i] !== "dismiss"}   onClick={() => setAction(i, "dismiss")}>무시</Btn>
                            </BtnRow>
                        </CandCard>
                    ))}

                    <ModalFooter>
                        <Muted>'앞으로도 적용'만 User Preference Store에 저장됩니다</Muted>
                        <Btn $primary disabled={submitting} onClick={handleSave}>
                            {submitting ? "저장 중..." : "선택 저장 후 닫기"}
                        </Btn>
                    </ModalFooter>
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
