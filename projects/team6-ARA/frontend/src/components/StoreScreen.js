import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { fetchStorage } from "../api/analyze";
import { mockStore } from "../mock";
import { Card, ScreenHead, StepNum, ScreenTitle, ScreenSub, TypeBadge, Pill, EmptyState, Table, MockNote, MockBadge } from "../styles/common";
import { theme } from "../styles/theme";

const TABS = [
    { key: "tasks",    label: "할 일" },
    { key: "calendar", label: "일정" },
    { key: "memo",     label: "메모" },
    { key: "risk",     label: "리스크" },
    { key: "pending",  label: "보류" },
];

const STORAGE_KIND = {
    tasks: "tasks",
    calendar: "calendar_events",
    memo: "memos",
    risk: "risk_logs",
    pending: "pending_queue",
};

export default function StoreScreen() {
    const [activeTab, setActiveTab] = useState("tasks");
    const [rowsByTab, setRowsByTab] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const storageKind = STORAGE_KIND[activeTab];
    const useMock = !storageKind || error;
    const rows = useMock ? mockStore[activeTab] : rowsByTab[activeTab] || [];

    useEffect(() => {
        if (!storageKind || rowsByTab[activeTab]) return;

        let cancelled = false;
        setLoading(true);
        setError(null);
        fetchStorage(storageKind)
            .then((data) => {
                if (cancelled) return;
                setRowsByTab((prev) => ({ ...prev, [activeTab]: data.rows || [] }));
            })
            .catch(() => {
                if (cancelled) return;
                setError("저장소 조회에 실패해 목데이터를 표시합니다.");
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [activeTab, rowsByTab, storageKind]);

    return (
        <div>
            <ScreenHead>
                <StepNum>5</StepNum>
                <ScreenTitle>로컬 저장소 보기</ScreenTitle>
                <ScreenSub>탭: 할 일 / 일정 / 메모 / 리스크 / 보류 / 선호</ScreenSub>
            </ScreenHead>

            <Card>
                {useMock && <MockBadge style={{ marginBottom: "10px" }} />}
                {loading && <MockNote>저장소를 불러오는 중입니다.</MockNote>}
                {error && <MockNote>{error}</MockNote>}
                <SubtabBar>
                    {TABS.map((tab) => {
                        const active = activeTab === tab.key;
                        return (
                            <Subtab key={tab.key} $active={active} onClick={() => setActiveTab(tab.key)}>
                                {tab.label}
                                <TabCount $active={active}>
                                    {active ? rows?.length ?? 0 : rowsByTab[tab.key]?.length ?? mockStore[tab.key]?.length ?? 0}
                                </TabCount>
                            </Subtab>
                        );
                    })}
                </SubtabBar>

                {activeTab === "tasks" && (
                    <Table>
                        <thead><tr><th>제목</th><th>담당</th><th>마감</th><th>우선순위</th><th>상태</th></tr></thead>
                        <tbody>
                            {rows.map((t) => (
                                <tr key={t.id}>
                                    <td>{t.title} {t.note && <Pill>{t.note}</Pill>}</td>
                                    <td>{t.assignee}</td>
                                    <td>{t.due_date || t.due || "—"}</td>
                                    <td><Pill $danger={t.priority === "high"}>{t.priority === "high" ? "높음" : "보통"}</Pill></td>
                                    <td>{t.status || "저장됨"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                )}

                {activeTab === "calendar" && (
                    <div>
                        {rows.map((c) => (
                            <CalRow key={c.id} $seed={c.seed}>
                                <CalWhen>
                                    <b>{c.time ?? "종일"}</b>
                                    {c.allDay && <span>all_day</span>}
                                </CalWhen>
                                <CalInfo>
                                    <b>{c.title}</b>{" "}
                                    {c.note && <Pill>{c.note}</Pill>}
                                    {c.seed && <Pill>기존(seed)</Pill>}
                                    <CalMeta>{c.date} · {c.assignee}</CalMeta>
                                </CalInfo>
                            </CalRow>
                        ))}
                    </div>
                )}

                {activeTab === "memo" && (
                    rows.length === 0 ? (
                        <EmptyState>
                            메모 저장소가 비어 있어요. ✎<br />
                            <span style={{ fontSize: "14px" }}>저장된 메모가 생기면 이 탭에 표시됩니다.</span>
                        </EmptyState>
                    ) : (
                        <Table>
                            <thead><tr><th>제목</th><th>내용</th></tr></thead>
                            <tbody>
                                {rows.map((m) => (
                                    <tr key={m.id}><td>{m.title}</td><td>{m.content || "—"}</td></tr>
                                ))}
                            </tbody>
                        </Table>
                    )
                )}

                {activeTab === "risk" && (
                    <Table>
                        <thead><tr><th>리스크</th><th>대응(mitigation)</th><th>출처 문장</th></tr></thead>
                        <tbody>
                            {rows.map((r) => (
                                <tr key={r.id}>
                                    <td>{r.title || r.description}</td>
                                    <td>{r.mitigation}</td>
                                    <SourceCell>{r.source ? `"${r.source}"` : "—"}</SourceCell>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                )}

                {activeTab === "pending" && (
                    <Table>
                        <thead><tr><th>항목</th><th>사유</th><th>확인 질문</th></tr></thead>
                        <tbody>
                            {rows.map((p) => (
                                <tr key={p.id}>
                                    <td>{p.title}</td>
                                    <td><PendingBadge>{p.reason || "보류"}</PendingBadge></td>
                                    <td>{p.clarification_question || p.question || "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                )}


                <MockNote style={{ marginTop: "16px" }}>
                    {useMock ? "※ 목데이터 표시 중" : `※ 실제 저장소 GET /storage/${storageKind} 응답`}
                </MockNote>
            </Card>
        </div>
    );
}

// ===== styled =====
const SubtabBar = styled.div`
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
    border-bottom: 2px solid ${theme.line};
    padding-bottom: 10px;
    margin-bottom: 16px;
`;

const Subtab = styled.button`
    font-size: 15px;
    border: 2px solid ${theme.line};
    background: ${({ $active }) => ($active ? theme.ink : "#fff")};
    color: ${({ $active }) => ($active ? "#fff" : theme.ink)};
    border-radius: 11px 8px 12px 7px;
    padding: 5px 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 7px;
    font-family: inherit;
`;

const TabCount = styled.span`
    font-size: 12px;
    background: ${({ $active }) => ($active ? "#fff" : theme.panel2)};
    border: 1.5px solid ${theme.hair};
    border-radius: 20px;
    padding: 0 7px;
    color: ${({ $active }) => ($active ? theme.ink : theme.ink2)};
`;

const CalRow = styled.div`
    display: flex;
    gap: 13px;
    align-items: flex-start;
    padding: 11px 12px;
    border: 2px solid ${theme.hair};
    background: #fff;
    border-radius: 11px;
    margin-bottom: 10px;
    opacity: ${({ $seed }) => ($seed ? 0.6 : 1)};
`;

const CalWhen = styled.div`
    font-size: 15px;
    text-align: center;
    flex: none;
    width: 80px;
    border-right: 2px dashed ${theme.hair};
    padding-right: 11px;

    b { display: block; font-size: 18px; color: ${theme.tCal}; }
`;

const CalInfo = styled.div`
    flex: 1;
    font-size: 13px;
`;

const CalMeta = styled.div`
    color: ${theme.muted};
    font-size: 12px;
    margin-top: 3px;
`;

const SourceCell = styled.td`
    font-style: italic;
    color: ${theme.ink2};
`;

const PendingBadge = styled.span`
    display: inline-flex;
    font-size: 13px;
    color: ${theme.warn};
    background: ${theme.warnbg};
    border: 2px solid ${theme.warn};
    border-radius: 8px;
    padding: 1px 9px;
`;
