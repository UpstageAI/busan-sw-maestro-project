package com.enderdragon.coach.gui;

import java.util.ArrayList;
import java.util.List;

/**
 * 코치 대화 기록(세션 단위). GUI를 열고 닫아도 유지되도록 정적으로 보관한다.
 *
 * <p>모든 읽기/쓰기는 클라이언트(게임) 스레드에서 일어난다고 가정한다
 * (비동기 응답은 {@code MinecraftClient#execute}로 게임 스레드에 올려 갱신).
 */
public final class CoachChatLog {

    /** 한 줄의 대화. {@code text}는 응답 대기 중 갱신될 수 있어 가변이다. */
    public static final class Message {
        public final boolean fromUser;
        public String text;

        Message(boolean fromUser, String text) {
            this.fromUser = fromUser;
            this.text = text;
        }
    }

    private static final List<Message> MESSAGES = new ArrayList<>();

    private CoachChatLog() {
    }

    public static List<Message> messages() {
        return MESSAGES;
    }

    public static Message addUser(String text) {
        Message m = new Message(true, text);
        MESSAGES.add(m);
        return m;
    }

    public static Message addCoach(String text) {
        Message m = new Message(false, text);
        MESSAGES.add(m);
        return m;
    }
}
