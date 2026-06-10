// 공통 styled-components
import styled from "styled-components";
import { theme, radius, shadow } from "./theme";

export const Wrap = styled.div`
    max-width: 960px;
    margin: 0 auto;
    padding: 28px 20px 80px;
`;

// ===== 카드 =====
export const Card = styled.div`
    background: ${theme.panel};
    border: 2.5px solid ${theme.line};
    border-radius: ${radius.card};
    box-shadow: ${shadow.card};
    padding: 26px 28px;
`;

// ===== 버튼 =====
export const Btn = styled.button`
    font-size: ${({ $sm }) => ($sm ? "13px" : "14px")};
    font-weight: 600;
    border: 2px solid ${({ $warn }) => ($warn ? theme.warn : theme.line)};
    background: ${({ $primary, $warn }) =>
        $primary ? theme.ink : $warn ? theme.warnbg : "#fff"};
    color: ${({ $primary, $warn }) =>
        $primary ? "#fff" : $warn ? theme.warn : theme.ink};
    border-radius: ${radius.btn};
    padding: ${({ $sm }) => ($sm ? "5px 12px" : "8px 18px")};
    cursor: pointer;
    box-shadow: ${shadow.btn};
    white-space: nowrap;
    font-family: inherit;
    letter-spacing: 0.01em;
    transition: opacity 0.1s, transform 0.08s;

    &:hover:not(:disabled) { opacity: 0.88; }
    &:active:not(:disabled) { transform: translate(1px, 2px); box-shadow: 1px 1px 0 rgba(0,0,0,.12); }
    &:disabled { opacity: .35; cursor: not-allowed; }
`;

export const BtnRow = styled.div`
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
`;

// ===== 화면 헤더 =====
export const ScreenHead = styled.div`
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
    flex-wrap: wrap;
`;

export const StepNum = styled.span`
    width: 40px;
    height: 40px;
    background: ${theme.ink};
    color: #fff;
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 18px;
    font-weight: 800;
    flex: none;
    letter-spacing: -0.5px;
`;

export const ScreenTitle = styled.h2`
    font-size: 22px;
    margin: 0;
    font-weight: 800;
    letter-spacing: -0.3px;
`;

export const ScreenSub = styled.span`
    color: ${theme.muted};
    font-size: 12.5px;
    margin-left: auto;
    line-height: 1.5;
`;

// ===== 배지 =====
const typeDotColor = {
    task:     theme.tTask,
    calendar: theme.tCal,
    memo:     theme.tMemo,
    risk:     theme.tRisk,
    pending:  theme.tPend,
    pend:     theme.tPend,
    input:    theme.note,
};

const typeBgColor = {
    task:     "#edf7f1",
    calendar: "#eaf2fb",
    memo:     "#f3f3f2",
    risk:     "#fcecea",
    pending:  "#fef3e2",
    pend:     "#fef3e2",
    input:    "#eef2fc",
};

export const TypeBadge = styled.span`
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    font-weight: 700;
    border: 1.5px solid ${({ type }) => typeDotColor[type] || theme.line};
    border-style: ${({ type }) => type === "input" ? "dashed" : "solid"};
    background: ${({ type }) => typeBgColor[type] || "#fff"};
    border-radius: ${radius.badge};
    padding: 3px 10px;
    color: ${({ type }) => typeDotColor[type] || theme.ink};
    letter-spacing: 0.01em;

    &::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: ${({ type }) => typeDotColor[type] || "transparent"};
        flex: none;
    }
`;

export const Pill = styled.span`
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    font-weight: 500;
    border: 1.5px solid ${({ $ok, $warn, $danger }) =>
        $ok ? theme.ok : $warn ? theme.warn : $danger ? theme.danger : theme.hair};
    background: ${({ $ok, $warn, $danger }) =>
        $ok ? "#edf7f1" : $warn ? theme.warnbg : $danger ? "#fcecea" : "#fff"};
    border-radius: 20px;
    padding: 2px 10px;
    color: ${({ $ok, $warn, $danger }) =>
        $ok ? theme.ok : $warn ? theme.warn : $danger ? theme.danger : theme.ink2};
`;

export const NeedsConfirm = styled.span`
    display: inline-flex;
    align-items: center;
    font-size: 12px;
    font-weight: 700;
    color: ${theme.warn};
    background: ${theme.warnbg};
    border: 1.5px solid ${theme.warn};
    border-radius: 8px;
    padding: 2px 10px;
    letter-spacing: 0.01em;
`;

// ===== 공통 박스 =====
export const WarnBox = styled.div`
    margin-top: 12px;
    background: ${theme.warnbg};
    border: 2px solid ${theme.warn};
    border-radius: 10px;
    padding: 11px 14px;
    font-size: 13px;
    line-height: 1.7;
    color: #6a4310;

    b { color: ${theme.warn}; }
`;

export const QBox = styled.div`
    margin-top: 10px;
    background: #eef3fb;
    border: 2px dashed ${theme.note};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    line-height: 1.6;
    color: #214a9e;
`;

export const EmptyState = styled.div`
    font-size: 15px;
    color: ${theme.muted};
    text-align: center;
    padding: 40px 10px;
    border: 2px dashed ${theme.hair};
    border-radius: 12px;
    background: #fff;
    line-height: 1.8;
`;

export const FieldLabel = styled.div`
    font-size: 15px;
    font-weight: 700;
    margin: 0 0 8px;
    color: ${({ warn }) => (warn ? theme.warn : theme.ink)};
    letter-spacing: 0.01em;
`;

export const MockNote = styled.p`
    font-size: 11.5px;
    color: ${theme.muted};
    margin: 10px 0 0;
    line-height: 1.5;
`;

// ===== 테이블 =====
export const Table = styled.table`
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    line-height: 1.5;

    th {
        text-align: left;
        padding: 9px 12px;
        font-size: 12px;
        font-weight: 700;
        color: ${theme.muted};
        border-bottom: 2px solid ${theme.line};
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    td {
        text-align: left;
        padding: 10px 12px;
        border-bottom: 1px solid ${theme.hair};
        color: ${theme.ink};
        vertical-align: middle;
    }

    tbody tr:nth-child(even) td { background: ${theme.paper}; }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr:hover td { background: ${theme.panel2}; transition: background 0.1s; }
`;

// ===== 목데이터 표시 =====
export const MockBadge = styled.span`
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: ${theme.muted};
    background: ${theme.panel2};
    border: 1.5px dashed ${theme.hair};
    border-radius: 6px;
    padding: 1px 7px;
    vertical-align: middle;

    &::before { content: "📋 목데이터"; }
`;

export const MockSection = styled.div`
    position: relative;
    border: 1.5px dashed ${theme.hair};
    border-radius: 10px;
    padding: 10px 12px;
    margin-top: 8px;

    &::after {
        content: "📋 목데이터";
        position: absolute;
        top: -10px;
        right: 10px;
        font-size: 11px;
        color: ${theme.muted};
        background: ${theme.panel};
        padding: 0 6px;
        border: 1.5px dashed ${theme.hair};
        border-radius: 6px;
    }
`;
