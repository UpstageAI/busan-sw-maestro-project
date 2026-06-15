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

// 단일 그래프 재개. 1차(승인)는 { decisions }, 2차(선호 확인)는 { preference_choices }.
// 그래프가 현재 정지점(1차/2차 interrupt)에 payload 를 주입한다.
export async function resumeRun(sessionId, payload) {
    const res = await fetch(`${API_URL}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, ...payload }),
    });
    if (!res.ok) throw new Error("승인 실행 실패");
    return res.json();
}

export async function fetchStorage(kind) {
    const res = await fetch(`${API_URL}/storage/${kind}`);
    if (!res.ok) throw new Error("저장소 조회 실패");
    return res.json();
}
