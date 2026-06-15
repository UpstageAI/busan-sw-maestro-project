import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { analyzeText, runItems } from "../api/analyze";
import { Card, Btn, BtnRow, ScreenHead, StepNum, ScreenTitle, ScreenSub } from "../styles/common";
import { theme, radius } from "../styles/theme";

const SAMPLE_TEXT =
    "내일까지 성종은 발표자료, 동근은 API 테스트 정리, 우태는 데모 영상 준비.\n" +
    "금요일 오전 10시 최종 리허설하자. 금요일에 팀 점심도 하자. " +
    "다음 주쯤 멘토님께 보여드리고, 안 되면 캘린더 연동은 Mock으로 대체하자. 기획서 다시 봐야 함.";

function getTodayKST() {
    return new Date()
        .toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit" })
        .replace(/\. /g, "-").replace(".", "");
}

function newSessionId() {
    return `session-${Date.now().toString(36)}`;
}

function flattenRunResult(analysisResult, runResult) {
    if (runResult.status !== "awaiting_approval") {
        return { ...analysisResult, session_id: runResult.session_id, run_result: runResult };
    }
    return {
        ...analysisResult,
        session_id: runResult.session_id,
        run_result: runResult,
        items: runResult.reviewables.map((reviewable) => ({
            ...reviewable.item,
            selection: reviewable.selection,
            conflict: reviewable.conflict,
        })),
        skipped: runResult.skipped,
    };
}

function getStageLabel(progress) {
    if (progress < 40) return "텍스트 분석 중…";
    if (progress < 75) return "항목 분류 중…";
    if (progress < 92) return "라우팅 처리 중…";
    if (progress < 100) return "충돌 검사 중…";
    return "완료";
}

export default function InputScreen({ onAnalyzeDone }) {
    const [text, setText] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [progress, setProgress] = useState(0);
    const intervalRef = useRef(null);

    function startFakeProgress() {
        setProgress(5);
        intervalRef.current = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 99) return prev;
                // 99에 가까울수록 느려짐
                const increment = (99 - prev) * 0.035;
                return Math.min(prev + increment, 99);
            });
        }, 200);
    }

    function stopFakeProgress() {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }

    useEffect(() => {
        return () => stopFakeProgress();
    }, []);

    async function handleAnalyze() {
        if (!text.trim()) return;
        setLoading(true);
        setError(null);
        startFakeProgress();

        try {
            const sessionId = newSessionId();
            const result = await analyzeText(text, getTodayKST());
            const runResult = await runItems(sessionId, result.items || [], text);

            // 완료 시 100%로 snap 후 페이지 전환
            stopFakeProgress();
            setProgress(100);
            await new Promise((r) => setTimeout(r, 500));

            const routedResult = flattenRunResult(result, runResult);
            onAnalyzeDone(routedResult, text);
        } catch (e) {
            stopFakeProgress();
            setProgress(0);
            setError("분석에 실패했습니다. 백엔드 서버가 실행 중인지 확인하세요.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div>
            <ScreenHead>
                <StepNum>1</StepNum>
                <ScreenTitle>입력</ScreenTitle>
                <ScreenSub>붙여넣기 → 분석 실행</ScreenSub>
            </ScreenHead>

            <Card>
                <AppHeader>
                    <AppLogo>⤳ Action Router Agent</AppLogo>
                    <KstBadge>기준 날짜(KST): <b>{getTodayKST()}</b></KstBadge>
                </AppHeader>

                <FieldLabel>텍스트 붙여넣기</FieldLabel>
                <TextInput
                    placeholder="회의록, 메신저 대화, 공지문, 메모를 붙여넣으세요."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    rows={8}
                    disabled={loading}
                />
                <CharCount>{text.length}자</CharCount>

                <BtnRow>
                    <Btn $primary onClick={handleAnalyze} disabled={loading || !text.trim()}>
                        {loading ? "분석 중…" : "분석 실행"}
                    </Btn>
                    <Btn $ghost onClick={() => setText(SAMPLE_TEXT)} disabled={loading}>샘플 불러오기</Btn>
                    <Btn $ghost onClick={() => setText("")} disabled={loading}>비우기</Btn>
                </BtnRow>

                {loading && (
                    <ProgressWrap>
                        <ProgressHeader>
                            <ProgressLabel>
                                <Spinner />
                                {getStageLabel(progress)}
                            </ProgressLabel>
                            <ProgressPct>{Math.floor(progress)}%</ProgressPct>
                        </ProgressHeader>
                        <ProgressTrack>
                            <ProgressFill $progress={progress} />
                        </ProgressTrack>
                    </ProgressWrap>
                )}

                {error && <ErrorBox>{error}</ErrorBox>}
            </Card>
        </div>
    );
}

// ===== styled =====
const AppHeader = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px dashed ${theme.hair};
    padding-bottom: 12px;
    margin-bottom: 16px;
`;

const AppLogo = styled.span`
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.3px;
    color: ${theme.ink};
`;

const KstBadge = styled.span`
    font-size: 12px;
    color: ${theme.ink2};
    border: 1.5px solid ${theme.hair};
    background: ${theme.paper};
    border-radius: 9px;
    padding: 4px 12px;
    line-height: 1;

    b { color: ${theme.ink}; font-weight: 700; }
`;

const FieldLabel = styled.div`
    font-size: 13px;
    font-weight: 700;
    margin: 0 0 8px;
    color: ${theme.muted};
    text-transform: uppercase;
    letter-spacing: 0.06em;
`;

const TextInput = styled.textarea`
    width: 100%;
    border: 2px solid ${theme.hair};
    border-radius: ${radius.input};
    padding: 14px 16px;
    font-size: 14px;
    font-family: inherit;
    line-height: 1.7;
    resize: vertical;
    background: #fff;
    color: ${theme.ink};
    margin-bottom: 8px;
    transition: border-color 0.15s;

    &::placeholder { color: ${theme.muted}; }
    &:focus { outline: none; border-color: ${theme.note}; box-shadow: 0 0 0 3px rgba(45,87,196,.08); }
`;

const CharCount = styled.div`
    font-size: 12px;
    color: ${theme.muted};
    margin-bottom: 14px;
    text-align: right;
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

const ProgressWrap = styled.div`
    margin-top: 16px;
`;

const ProgressHeader = styled.div`
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
`;

const ProgressLabel = styled.span`
    font-size: 13px;
    color: ${theme.ink2};
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
`;

const Spinner = styled.span`
    width: 14px;
    height: 14px;
    border: 2px solid ${theme.hair};
    border-top-color: ${theme.ink};
    border-radius: 50%;
    display: inline-block;
    animation: spin 0.7s linear infinite;

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;

const ProgressPct = styled.span`
    font-size: 12px;
    color: ${theme.muted};
`;

const ProgressTrack = styled.div`
    width: 100%;
    height: 8px;
    background: ${theme.panel2};
    border-radius: 99px;
    border: 1.5px solid ${theme.hair};
    overflow: hidden;
`;

const ProgressFill = styled.div`
    height: 100%;
    width: ${({ $progress }) => $progress}%;
    background: ${theme.ink};
    border-radius: 99px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
`;
