package com.enderdragon.coach.api;

/** 백엔드 호출 실패를 채팅에 사용자 친화적으로 안내하기 위한 예외. */
public class CoachApiException extends RuntimeException {

    public CoachApiException(String message) {
        super(message);
    }

    public CoachApiException(String message, Throwable cause) {
        super(message, cause);
    }
}
