package com.enderdragon.coach.config;

import java.util.UUID;

/**
 * 모드 설정값. 지금은 백엔드 주소와 세션(thread_id) 정도만 관리한다.
 *
 * <p>백엔드 주소는 JVM 시스템 프로퍼티 {@code -Dcoach.backend.url=...} 또는
 * 환경변수 {@code COACH_BACKEND_URL}로 덮어쓸 수 있다. 둘 다 없으면 로컬 기본값을 쓴다.
 * (정식 설정 파일 UI는 4·5번 단계에서 확장)
 */
public final class CoachConfig {

    private static final String DEFAULT_BACKEND_URL = "http://localhost:8001";

    /** 게임 실행 동안 대화 맥락을 잇기 위한 세션 식별자. 백엔드의 thread_id로 전달된다. */
    private static final String SESSION_THREAD_ID = "mc-" + UUID.randomUUID();

    private CoachConfig() {
    }

    /** 백엔드 base URL (끝 슬래시 없음). */
    public static String backendUrl() {
        String fromProperty = System.getProperty("coach.backend.url");
        if (fromProperty != null && !fromProperty.isBlank()) {
            return trimTrailingSlash(fromProperty);
        }
        String fromEnv = System.getenv("COACH_BACKEND_URL");
        if (fromEnv != null && !fromEnv.isBlank()) {
            return trimTrailingSlash(fromEnv);
        }
        return DEFAULT_BACKEND_URL;
    }

    /** 이번 게임 세션의 thread_id. */
    public static String threadId() {
        return SESSION_THREAD_ID;
    }

    private static String trimTrailingSlash(String url) {
        String trimmed = url.strip();
        return trimmed.endsWith("/") ? trimmed.substring(0, trimmed.length() - 1) : trimmed;
    }
}
