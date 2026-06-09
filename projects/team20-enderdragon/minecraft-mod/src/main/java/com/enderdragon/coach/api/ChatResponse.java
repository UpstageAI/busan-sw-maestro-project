package com.enderdragon.coach.api;

import java.util.List;

/**
 * 백엔드 {@code POST /api/v1/chat/sync} 응답 바디.
 * 백엔드 스키마(app/schemas.py: ChatResponse)와 필드를 맞춘다.
 */
public class ChatResponse {

    public String answer;
    public String domain;
    public List<String> sources;
    public String disclaimer;
    /** 게임 할 일 목록용 짧은 명령형 TODO (웹은 빈 배열). 비어 있으면 모드가 answer 파싱으로 폴백. */
    public List<String> todos;

    /** 코치 답변 본문. null 방지용 헬퍼. */
    public String answerOrEmpty() {
        return answer == null ? "" : answer;
    }

    /** 백엔드가 만든 짧은 TODO가 있으면 true. */
    public boolean hasTodos() {
        return todos != null && !todos.isEmpty();
    }
}
