import React from "react";
import styled from "styled-components";
import { theme } from "../styles/theme";

export default function AgentLog() {
    return (
        <LogWrap>
            <LogToggle disabled>
                ◧ Agent 실행 로그 <DisabledBadge>미지원</DisabledBadge>
            </LogToggle>
        </LogWrap>
    );
}

// ===== styled =====
const LogWrap = styled.div`
    margin-top: 20px;
`;

const LogToggle = styled.button`
    width: 100%;
    text-align: left;
    font-size: 14px;
    color: ${theme.muted};
    background: ${theme.panel2};
    border: 2px solid ${theme.hair};
    border-radius: 10px;
    padding: 8px 14px;
    cursor: not-allowed;
    font-family: inherit;
    display: flex;
    align-items: center;
    gap: 8px;
    opacity: 0.6;
`;

const DisabledBadge = styled.span`
    font-size: 11px;
    color: ${theme.muted};
    background: ${theme.panel};
    border: 1.5px dashed ${theme.hair};
    border-radius: 6px;
    padding: 1px 7px;
`;
