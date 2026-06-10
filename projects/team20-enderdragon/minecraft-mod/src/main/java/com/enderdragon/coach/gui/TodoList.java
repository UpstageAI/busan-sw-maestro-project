package com.enderdragon.coach.gui;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class TodoList {

    public static final class TodoItem {
        public final String shortText; // HUD용 초간소화
        public final String fullText;  // TodoScreen용 필터링 원문

        TodoItem(String shortText, String fullText) {
            this.shortText = shortText;
            this.fullText  = fullText;
        }
    }

    private static final List<TodoItem> ITEMS = new ArrayList<>();

    // ── shortText: 동사 어간 → 표시 형태 ────────────────────────────────
    private static final Map<String, String> VERB_DISPLAY = new LinkedHashMap<>();
    static {
        VERB_DISPLAY.put("만들", "만들기");
        VERB_DISPLAY.put("제작", "제작");
        VERB_DISPLAY.put("수집", "수집");
        VERB_DISPLAY.put("채굴", "채굴");
        VERB_DISPLAY.put("파괴", "파괴");
        VERB_DISPLAY.put("건축", "건축");
        VERB_DISPLAY.put("탐험", "탐험");
        VERB_DISPLAY.put("이동", "이동");
        VERB_DISPLAY.put("사냥", "사냥");
        VERB_DISPLAY.put("수확", "수확");
        VERB_DISPLAY.put("설치", "설치");
        VERB_DISPLAY.put("배치", "배치");
        VERB_DISPLAY.put("착용", "착용");
        VERB_DISPLAY.put("찾", "찾기");
        VERB_DISPLAY.put("얻", "얻기");
        VERB_DISPLAY.put("먹", "먹기");
        VERB_DISPLAY.put("캐", "캐기");
    }

    // 폴백용 한국어 시퀀스 추출 패턴
    private static final Pattern FIRST_KOREAN = Pattern.compile("[가-힣]+");

    // ── fullText: 불필요 텍스트 필터 패턴 ────────────────────────────────
    private static final Pattern FILTER_BRACKETS  = Pattern.compile("\\[.*?]");
    private static final Pattern FILTER_WIKI_PAREN = Pattern.compile("\\(.*?위키.*?\\)");
    private static final Pattern FILTER_REF_PAREN  = Pattern.compile("\\(참고[^)]*\\)");

    private TodoList() {}

    public static List<TodoItem> items() {
        return Collections.unmodifiableList(ITEMS);
    }

    /**
     * 백엔드가 만든 짧은 TODO 목록을 그대로 등록한다. (게임 모드 경로)
     * 이미 짧은 명령형이라 압축(toShort) 없이 HUD·목록에 동일 텍스트를 쓴다.
     */
    public static void addAll(List<String> todos) {
        if (todos == null) return;
        for (String todo : todos) {
            if (todo == null) continue;
            String clean = cleanTodo(todo);
            if (clean.isEmpty()) continue;
            ITEMS.add(new TodoItem(clean, clean));
        }
    }

    // 백엔드 todo에 혹시 남은 불릿/번호/마크다운 강조 제거
    private static String cleanTodo(String s) {
        String t = s.strip();
        t = t.replaceFirst("^[-*•]\\s*", "");        // 불릿
        t = t.replaceFirst("^\\d+\\s*[.)]\\s*", ""); // 번호
        return t.replace("**", "").strip();          // 마크다운 강조
    }

    public static void parseAndAdd(String answer) {
        if (answer == null || answer.isBlank()) return;
        for (String line : answer.split("\\r?\\n")) {
            String trimmed = line.stripLeading();
            if (trimmed.startsWith("- ") && trimmed.length() > 2) {
                String raw = trimmed.substring(2).strip();
                // N단계: 접두사 제거
                raw = raw.replaceFirst("^\\d+\\s*단계\\s*[:.\\-)\\s]*", "").strip();
                if (raw.isEmpty()) continue;

                String fullText  = toFull(raw);
                String shortText = toShort(fullText);
                ITEMS.add(new TodoItem(shortText, fullText));
            }
        }
    }

    // [위키] / (마인크래프트 위키) / (참고: ...) 제거
    private static String toFull(String text) {
        text = FILTER_BRACKETS.matcher(text).replaceAll("").strip();
        text = FILTER_WIKI_PAREN.matcher(text).replaceAll("").strip();
        text = FILTER_REF_PAREN.matcher(text).replaceAll("").strip();
        return text;
    }

    // 첫 번째 동사 어간 탐색 → 공백 분리 토큰에서 명사 추출 → "명사 동사표시" 조합
    private static String toShort(String text) {
        // 1. VERB_DISPLAY 순서대로 첫 번째 동사 어간 탐색
        String foundStem = null, foundDisplay = null;
        for (Map.Entry<String, String> e : VERB_DISPLAY.entrySet()) {
            if (text.contains(e.getKey())) {
                foundStem    = e.getKey();
                foundDisplay = e.getValue();
                break;
            }
        }

        // 2. 공백 기준 토큰에서 첫 번째 '한국어 포함 & 동사 아닌' 토큰을 명사로 선택
        String noun = null;
        for (String token : text.split("\\s+")) {
            String t = token.replaceAll("[을를이가]$", ""); // 조사 제거
            if (!t.matches(".*[가-힣].*")) continue;       // 한국어 없으면 스킵 (숫자 등)
            if (foundStem != null && t.contains(foundStem)) continue; // 동사 포함 토큰 스킵
            noun = t;
            break;
        }

        if (noun != null && foundDisplay != null) return noun + " " + foundDisplay;
        if (foundDisplay != null)                 return foundDisplay;

        // 3. 폴백: 첫 번째 한국어 시퀀스 (최대 8자)
        Matcher m = FIRST_KOREAN.matcher(text);
        if (m.find()) {
            String s = m.group();
            return s.length() > 8 ? s.substring(0, 8) : s;
        }
        return text.length() > 8 ? text.substring(0, 8) : text;
    }

    public static void complete(int index) {
        if (index >= 0 && index < ITEMS.size()) {
            ITEMS.remove(index);
        }
    }

    public static void completeAll() {
        ITEMS.clear();
    }

    public static boolean isEmpty() {
        return ITEMS.isEmpty();
    }
}
