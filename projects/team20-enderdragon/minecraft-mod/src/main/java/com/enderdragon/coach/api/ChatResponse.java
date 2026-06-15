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
    /** 제작 목표가 있을 때만 채워지는 3×3 제작법 격자. 없으면 null. */
    public Recipe recipe;

    /** 코치 답변 본문. null 방지용 헬퍼. */
    public String answerOrEmpty() {
        return answer == null ? "" : answer;
    }

    /** 백엔드가 만든 짧은 TODO가 있으면 true. */
    public boolean hasTodos() {
        return todos != null && !todos.isEmpty();
    }

    /** 렌더링할 제작법 격자가 있으면 true. */
    public boolean hasRecipe() {
        return recipe != null && recipe.grid != null && !recipe.grid.isEmpty();
    }

    /**
     * 제작법 3×3 격자 (백엔드 schemas.py: RecipeGrid와 필드를 맞춘다).
     *
     * <p>{@code grid}는 9칸(행 우선, 좌상단 정렬)으로 각 칸은 아이템 ID 문자열 또는 빈 칸(null).
     * 태그 재료는 백엔드가 대표 구체 아이템으로 이미 치환해 보낸다.
     */
    public static class Recipe {
        public String output;     // 결과물 item id (예: minecraft:iron_pickaxe)
        public int count;         // 결과 개수
        public List<String> grid; // 9칸(item_id 또는 null)
    }
}
