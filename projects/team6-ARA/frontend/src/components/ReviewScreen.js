import React, { useState } from "react";
import styled from "styled-components";
import ItemCard from "./ItemCard";
import AgentLog from "./AgentLog";
import { Card, Btn, BtnRow, ScreenHead, StepNum, ScreenTitle, ScreenSub, TypeBadge, Pill } from "../styles/common";
import { theme } from "../styles/theme";

export default function ReviewScreen({ result, onDone }) {
    const [items, setItems] = useState(result.items || []);
    const [approved, setApproved] = useState([]);
    const [excluded, setExcluded] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const pending = items.filter((it) => !approved.includes(it) && !excluded.includes(it));
    const conflictCount = items.filter((it) => it.conflict?.has_conflict).length;
    const needsConfirmCount = items.filter((it) => it.needs_confirmation).length;

    function handleApprove(item) { setApproved((p) => [...p, item]); }
    function handleExclude(item) { setExcluded((p) => [...p, item]); }
    function handleEdit(original, edited) {
        // 수정 표시. 원본/수정 diff 는 그래프(feedback_analyze)가 BE 에서 계산한다.
        setItems((p) => p.map((it) => (it === original ? { ...it, ...edited, _modified: true } : it)));
    }
    function handleApproveAll() { setApproved([...items]); }

    async function handleDone() {
        setSubmitting(true);
        setError(null);
        try {
            await onDone(approved, excluded);
        } catch (e) {
            setError("승인 실행에 실패했습니다. 백엔드 서버와 세션 상태를 확인하세요.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div>
            <ScreenHead>
                <StepNum>2</StepNum>
                <ScreenTitle>
                    분석 결과 &amp; 승인
                    <ImportantBadge>★ 가장 중요</ImportantBadge>
                </ScreenTitle>
                <ScreenSub>분해된 항목 · 판단 근거 · 라우팅 이유 · 충돌/확인필요 · 승인/수정/제외</ScreenSub>
            </ScreenHead>

            <Card>
                <SummaryBar>
                    <SummaryText>
                        실행 항목 <b>{items.length}</b>개 분해됨
                        {conflictCount > 0 && ` · 충돌 ${conflictCount}`}
                        {needsConfirmCount > 0 && ` · 확인 필요 ${needsConfirmCount}`}
                    </SummaryText>
                    <Btn $primary onClick={handleApproveAll}>✓ 전체 승인</Btn>
                </SummaryBar>

                <ProgressRow>
                    <Pill $ok>✓ 승인 {approved.length}</Pill>
                    <Pill>대기 {pending.length}</Pill>
                    <Pill $warn>제외 {excluded.length}</Pill>
                </ProgressRow>

                {pending.map((item, i) => (
                    <ItemCard key={i} item={item} onApprove={handleApprove} onExclude={handleExclude} onEdit={handleEdit} />
                ))}

                {pending.length === 0 && <EmptyMsg>모든 항목을 처리했어요.</EmptyMsg>}

                {approved.length > 0 && (
                    <ApprovedPreview>
                        <ApprovedLabel>✓ 승인된 항목 ({approved.length})</ApprovedLabel>
                        {approved.map((item, i) => (
                            <ApprovedRow key={i}>
                                <TypeBadge type={item.type}>{item.type}</TypeBadge>
                                <span>{item.title}</span>
                            </ApprovedRow>
                        ))}
                    </ApprovedPreview>
                )}

                <AgentLog />

                {error && <ErrorBox>{error}</ErrorBox>}

                <BtnRow style={{ marginTop: "20px" }}>
                    <Btn $primary onClick={handleDone} disabled={submitting || approved.length === 0}>
                        {submitting ? "저장 실행 중…" : "선호 확인 →"}
                    </Btn>
                </BtnRow>
            </Card>
        </div>
    );
}

// ===== styled =====
const ImportantBadge = styled.span`
    font-size: 13px;
    color: ${theme.warn};
    font-weight: 400;
    margin-left: 8px;
`;

const SummaryBar = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 10px;
`;

const SummaryLeft = styled.div`
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
`;

const SummaryText = styled.span`
    font-size: 13px;
    color: ${theme.ink2};

    b { color: ${theme.ink}; }
`;

const ProgressRow = styled.div`
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
`;

const EmptyMsg = styled.div`
    text-align: center;
    color: ${theme.muted};
    padding: 24px;
    font-size: 15px;
`;

const ErrorBox = styled.div`
    margin-top: 12px;
    background: ${theme.warnbg};
    border: 2px solid ${theme.warn};
    border-radius: 10px;
    padding: 10px 13px;
    color: ${theme.warn};
    font-size: 13px;
`;

const ApprovedPreview = styled.div`
    margin-top: 16px;
    padding: 12px;
    background: ${theme.panel2};
    border-radius: 10px;
    border: 1.5px dashed ${theme.hair};
`;

const ApprovedLabel = styled.div`
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 8px;
`;

const ApprovedRow = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 13px;
`;
