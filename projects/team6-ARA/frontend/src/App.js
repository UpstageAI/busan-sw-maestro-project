import React, { useState } from "react";
import styled from "styled-components";
import GlobalStyle from "./styles/GlobalStyle";
import { Wrap } from "./styles/common";
import { theme, radius, shadow } from "./styles/theme";
import InputScreen from "./components/InputScreen";
import ReviewScreen from "./components/ReviewScreen";
import PreferenceModal from "./components/PreferenceModal";
import SummaryScreen from "./components/SummaryScreen";
import StoreScreen from "./components/StoreScreen";
import { resumeRun } from "./api/analyze";

const STEPS = [
    { id: "input",      label: "입력",      num: 1 },
    { id: "review",     label: "분석·승인", num: 2 },
    { id: "preference", label: "선호 확인", num: 3 },
    { id: "summary",    label: "결과 요약", num: 4 },
    { id: "store",      label: "저장소 보기", num: 5 },
];

// ===== styled =====
const AppTop = styled.header`
    margin-bottom: 14px;
    padding-bottom: 14px;
    border-bottom: 2px dashed ${theme.hair};
`;

const BrandH1 = styled.h1`
    font-size: 24px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
    color: ${theme.ink};
`;

const BrandP = styled.p`
    margin: 4px 0 0;
    color: ${theme.muted};
    font-size: 12.5px;
`;

const FlowNav = styled.nav`
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    padding: 10px 14px;
    background: ${theme.panel};
    border: 2px solid ${theme.line};
    border-radius: 18px 14px 20px 12px;
    box-shadow: ${shadow.card};
    margin-bottom: 26px;
`;

const FlowTab = styled.button`
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 13.5px;
    font-weight: ${({ $active }) => ($active ? "700" : "500")};
    border: 2px solid ${({ $active }) => ($active ? theme.ink : theme.hair)};
    background: ${({ $active }) => ($active ? theme.ink : "#fff")};
    color: ${({ $active }) => ($active ? "#fff" : theme.ink2)};
    border-radius: ${radius.btn};
    padding: 6px 13px;
    cursor: pointer;
    font-family: inherit;
    transition: border-color 0.1s, color 0.1s;

    &:hover:not([style*="active"]) {
        border-color: ${theme.line};
        color: ${theme.ink};
    }
`;

const FlowNum = styled.span`
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1.5px solid ${({ $active }) => ($active ? "#fff" : theme.hair)};
    display: grid;
    place-items: center;
    font-size: 12px;
    font-weight: 700;
    background: ${({ $active }) => ($active ? "#fff" : theme.paper)};
    color: ${({ $active }) => ($active ? theme.ink : theme.muted)};
`;

const FlowArrow = styled.span`
    color: ${theme.hair};
    font-size: 16px;
`;

const MainContent = styled.main`
    animation: fade 0.2s ease;
    @keyframes fade {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: none; }
    }
`;

// ===== App =====
export default function App() {
    const [step, setStep] = useState("input");
    const [analyzeResult, setAnalyzeResult] = useState(null);
    const [rawText, setRawText] = useState("");
    const [approved, setApproved] = useState([]);
    const [excluded, setExcluded] = useState([]);
    const [executionResult, setExecutionResult] = useState(null);
    const [preferenceCandidates, setPreferenceCandidates] = useState([]);

    function handleAnalyzeDone(result, text) {
        setAnalyzeResult(result);
        setRawText(text);
        // /run 이 검토할 항목 없이 바로 완료된 경우(전부 ignore 등) 승인 단계를 건너뛴다.
        if (result.run_result?.status === "completed") {
            setExecutionResult(result.run_result);
            setStep("summary");
            return;
        }
        setStep("review");
    }

    function cleanItem(item) {
        const { selection, conflict, _modified, ...cleaned } = item;
        return cleaned;
    }

    async function handleReviewDone(approvedItems, excludedItems) {
        setApproved(approvedItems);
        setExcluded(excludedItems);
        setExecutionResult(null);
        setPreferenceCandidates([]);

        const sessionId = analyzeResult?.session_id;
        if (!sessionId) {
            setStep("summary");
            return;
        }

        // 1차 resume — 승인 결정으로 그래프 재개. modify 가 있으면 그래프가
        // 2차(선호 확인) interrupt 로 정지하며 candidates 를 돌려준다.
        const decisions = [
            ...approvedItems.map((item, idx) => ({
                item_id: item.id || `item-${idx}`,
                action: item._modified ? "modify" : "approve",
                modified_item: item._modified ? cleanItem(item) : undefined,
            })),
            ...excludedItems.map((item, idx) => ({
                item_id: item.id || `item-${idx}`,
                action: "exclude",
            })),
        ];
        const result = await resumeRun(sessionId, { decisions });
        setExecutionResult(result);

        if (result.status === "awaiting_preference") {
            setPreferenceCandidates(result.candidates || []);
            setStep("preference");
        } else {
            // 수정 항목이 없어 선호 후보가 없으면 그래프가 바로 완료된다.
            setStep("summary");
        }
    }

    function handlePreferenceDone(result) {
        // PreferenceModal 이 2차 resume(preference_choices)까지 수행한 뒤 결과를 넘긴다.
        if (result) setExecutionResult(result);
        setStep("summary");
    }

    function handleRestart() {
        setStep("input");
        setAnalyzeResult(null);
        setRawText("");
        setApproved([]);
        setExcluded([]);
        setExecutionResult(null);
        setPreferenceCandidates([]);
    }

    return (
        <>
            <GlobalStyle />
            <Wrap>
                <AppTop>
                    <BrandH1>Action Router Agent</BrandH1>
                    <BrandP>비정형 텍스트 → 실행 항목 분해·분류·라우팅 · 로컬 데모</BrandP>
                </AppTop>

                <FlowNav>
                    {STEPS.map((s, i) => {
                        const active = step === s.id;
                        return (
                            <React.Fragment key={s.id}>
                                <FlowTab
                                    $active={active}
                                    onClick={() => {
                                        if (s.id === "input") handleRestart();
                                        if (s.id === "store") setStep("store");
                                    }}
                                >
                                    <FlowNum $active={active}>{s.num}</FlowNum>
                                    {s.label}
                                </FlowTab>
                                {i < STEPS.length - 1 && <FlowArrow>→</FlowArrow>}
                            </React.Fragment>
                        );
                    })}
                </FlowNav>

                <MainContent>
                    {step === "input" && (
                        <InputScreen onAnalyzeDone={handleAnalyzeDone} />
                    )}
                    {step === "review" && analyzeResult && (
                        <ReviewScreen
                            result={analyzeResult}
                            rawText={rawText}
                            onDone={handleReviewDone}
                        />
                    )}
                    {step === "preference" && (
                        <PreferenceModal
                            sessionId={analyzeResult?.session_id}
                            candidates={preferenceCandidates}
                            onDone={handlePreferenceDone}
                        />
                    )}
                    {step === "summary" && (
                        <SummaryScreen
                            approved={approved}
                            excluded={excluded}
                            executionResult={executionResult}
                            onGoStore={() => setStep("store")}
                            onRestart={handleRestart}
                        />
                    )}
                    {step === "store" && <StoreScreen />}
                </MainContent>
            </Wrap>
        </>
    );
}
