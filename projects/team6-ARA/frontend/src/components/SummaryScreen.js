import React from "react";
import styled from "styled-components";
import { Card, Btn, BtnRow, ScreenHead, StepNum, ScreenTitle, ScreenSub, TypeBadge, NeedsConfirm, QBox, Table, MockNote } from "../styles/common";
import { theme } from "../styles/theme";

const TYPE_LABEL  = { task: "할 일", calendar: "일정", memo: "메모", risk: "리스크", pending: "보류" };
const STORE_LABEL = { task: "Task Store", calendar: "Calendar", memo: "Memo Store", risk: "Risk Log", pending: "Pending" };

function displaySchedule(item) {
    const date = item.type === "task" ? item.due_date : item.date;
    if (date && item.time) return `${date} ${item.time}`;
    return date || item.time || "—";
}

export default function SummaryScreen({ approved, excluded, executionResult, onGoStore, onRestart }) {
    const saved   = approved.filter((it) => it.type !== "pending");
    const pending = approved.filter((it) => it.type === "pending");
    const summary = executionResult?.summary;
    const savedCount = summary?.executed ?? saved.length;
    const pendingCount = summary?.failed ?? pending.length;
    const excludedCount = summary?.excluded ?? excluded.length;

    return (
        <div>
            <ScreenHead>
                <StepNum>4</StepNum>
                <ScreenTitle>저장 결과 요약</ScreenTitle>
                <ScreenSub>저장된 항목 요약 · 보류 항목 별도 구분</ScreenSub>
            </ScreenHead>

            <Card>
                <StatGrid>
                    <Stat><StatBig $variant="ok">{savedCount}</StatBig><StatCap>✓ 저장 성공</StatCap></Stat>
                    <Stat><StatBig $variant="pend">{pendingCount}</StatBig><StatCap>⏸ 보류(Pending)</StatCap></Stat>
                    <Stat><StatBig $variant="skip">{excludedCount}</StatBig><StatCap>— 제외</StatCap></Stat>
                </StatGrid>

                {saved.length > 0 && (
                    <>
                        <SectionLabel>✓ 저장된 항목</SectionLabel>
                        <Table>
                            <thead><tr><th>유형</th><th>제목</th><th>담당</th><th>마감/일시</th><th>저장소</th></tr></thead>
                            <tbody>
                                {saved.map((item, i) => (
                                    <tr key={i}>
                                        <td><TypeBadge type={item.type}>{TYPE_LABEL[item.type]}</TypeBadge></td>
                                        <td>{item.title}</td>
                                        <td>{item.assignee || "—"}</td>
                                        <td>{displaySchedule(item)}</td>
                                        <td>{STORE_LABEL[item.type]}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>
                    </>
                )}

                {pending.length > 0 && (
                    <>
                        <SectionLabel $warn>⏸ 보류 항목</SectionLabel>
                        {pending.map((item, i) => (
                            <PendingCard key={i}>
                                <PendingHeader>
                                    <TypeBadge type="pending">보류</TypeBadge>
                                    <b>{item.title}</b>
                                    <NeedsConfirm>확인 필요</NeedsConfirm>
                                </PendingHeader>
                                {item.clarification_question && (
                                    <QBox>확인 질문: <b>"{item.clarification_question}"</b></QBox>
                                )}
                            </PendingCard>
                        ))}
                    </>
                )}

                <NextRow>
                    <Muted>다음 단계 →</Muted>
                    <BtnRow>
                        <Btn $primary onClick={onGoStore}>저장소 보기</Btn>
                        <Btn $ghost $sm onClick={onRestart}>새 텍스트 분석</Btn>
                    </BtnRow>
                </NextRow>

                {executionResult ? (
                    <MockNote>※ 저장 실행 결과는 POST /resume 응답 기준입니다.</MockNote>
                ) : (
                    <MockNote>※ 저장 실행 결과 없음 · 프론트 state 기준으로 표시 중</MockNote>
                )}
            </Card>
        </div>
    );
}

// ===== styled =====
const StatGrid = styled.div`
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 6px;

    @media (max-width: 680px) { grid-template-columns: 1fr; }
`;

const Stat = styled.div`
    background: #fff;
    border: 2px solid ${theme.line};
    border-radius: 13px 10px 14px 9px;
    padding: 14px;
    box-shadow: 2px 3px 0 rgba(0,0,0,.07);
`;

const StatBig = styled.div`
    font-size: 34px;
    font-weight: 700;
    line-height: 1;
    color: ${({ $variant }) =>
        $variant === "ok" ? theme.ok : $variant === "pend" ? theme.warn : theme.muted};
`;

const StatCap = styled.div`
    color: ${theme.ink2};
    font-size: 12.5px;
    margin-top: 4px;
`;

const SectionLabel = styled.div`
    font-size: 16px;
    font-weight: 700;
    margin: 18px 0 8px;
    color: ${({ $warn }) => ($warn ? theme.warn : theme.ink)};
`;

const PendingCard = styled.div`
    background: #fff;
    border: 2px solid ${theme.warn};
    border-radius: 13px 10px 14px 9px;
    padding: 14px 15px;
    margin-bottom: 12px;
`;

const PendingHeader = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
`;

const NextRow = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 20px;
    flex-wrap: wrap;
    gap: 10px;
`;

const Muted = styled.span`
    font-size: 13px;
    color: ${theme.ink2};
`;
