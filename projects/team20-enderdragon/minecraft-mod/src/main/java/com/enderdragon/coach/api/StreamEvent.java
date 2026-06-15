package com.enderdragon.coach.api;

/**
 * 백엔드 SSE({@code POST /api/v1/chat}) 스트림의 한 이벤트.
 * 백엔드 스키마(app/schemas.py: StreamEvent)와 필드를 맞춘다.
 *
 * <p>{@code data}는 이벤트 종류에 따라 다르다:
 * <ul>
 *   <li>{@code event="token"} → 응답 토큰 텍스트 조각</li>
 *   <li>{@code event="done"}  → 완료 페이로드(JSON 문자열: answer·domain·sources·todos·recipe)</li>
 *   <li>{@code event="node"}  → 노드 출력(JSON 문자열) — 모드는 사용하지 않음</li>
 * </ul>
 */
public class StreamEvent {
    public String event;
    public String node;
    public String data;
}
