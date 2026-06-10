// POST /analyze 실제 연동

function defaultApiUrl() {
    if (typeof window === "undefined") return "http://localhost:8000";
    return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_URL = process.env.REACT_APP_API_URL || defaultApiUrl();

export async function analyzeText(rawText, baseDate) {
    const res = await fetch(`${API_URL}/analyze/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: rawText, base_date: baseDate }),
    });
    if (!res.ok) throw new Error("분석 요청 실패");
    return res.json();
}

export async function runItems(sessionId, items, rawInput) {
    const res = await fetch(`${API_URL}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, items, raw_input: rawInput }),
    });
    if (!res.ok) throw new Error("라우팅 요청 실패");
    return res.json();
}

export async function resumeRun(sessionId, decisions) {
    const res = await fetch(`${API_URL}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, decisions }),
    });
    if (!res.ok) throw new Error("승인 실행 실패");
    return res.json();
}

export async function fetchStorage(kind) {
    const res = await fetch(`${API_URL}/storage/${kind}`);
    if (!res.ok) throw new Error("저장소 조회 실패");
    return res.json();
}

export async function analyzeFeedback(sessionId, original, modified) {
    const res = await fetch(`${API_URL}/feedback/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, original, modified }),
    });
    if (!res.ok) throw new Error("피드백 분석 실패");
    return res.json();
}

export async function confirmFeedback(sessionId, logId, action, candidates) {
    const res = await fetch(`${API_URL}/feedback/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, log_id: logId, action, candidates }),
    });
    if (!res.ok) throw new Error("선호 저장 실패");
    return res.json();
}
