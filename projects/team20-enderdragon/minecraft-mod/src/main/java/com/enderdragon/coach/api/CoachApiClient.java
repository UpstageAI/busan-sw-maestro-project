package com.enderdragon.coach.api;

import com.enderdragon.coach.config.CoachConfig;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.stream.Stream;

/**
 * 백엔드 코칭 에이전트 API 클라이언트.
 *
 * <p>게임 스레드를 막지 않도록 비동기({@link CompletableFuture})로 호출한다.
 * 호출자는 결과를 받은 뒤 반드시 게임(클라이언트) 스레드에서 채팅 출력을 해야 한다.
 */
public final class CoachApiClient {

    private static final Gson GSON = new Gson();

    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    private CoachApiClient() {
    }

    /**
     * 코치에게 메시지를 보내고 응답을 비동기로 받는다.
     *
     * @param message   사용자가 입력한 질문 (예: "이제 뭐 해야 해?")
     * @param inventory 현재 플레이어 인벤토리 (null이면 빈 리스트로 처리)
     * @param gameState 현재 인게임 상태(시간·체력·좌표 등, null이면 미전송)
     * @return 백엔드 응답을 담은 future. 실패 시 {@link CoachApiException}로 완료된다.
     */
    public static CompletableFuture<ChatResponse> chat(String message,
                                                       List<InventorySnapshot.InventoryItem> inventory,
                                                       GameStateSnapshot.GameState gameState) {
        final String url = CoachConfig.backendUrl() + "/api/v1/chat/sync";
        final String payload = GSON.toJson(new ChatRequest(message, CoachConfig.threadId(), inventory, gameState));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(60))
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload, StandardCharsets.UTF_8))
                .build();

        return HTTP.sendAsync(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8))
                .handle((response, error) -> {
                    if (error != null) {
                        throw new CoachApiException(
                                "백엔드에 연결하지 못했어요. 서버가 켜져 있는지 확인해 주세요 (" + url + ")", error);
                    }
                    int status = response.statusCode();
                    if (status / 100 != 2) {
                        throw new CoachApiException("백엔드 응답 오류 (HTTP " + status + ")");
                    }
                    try {
                        ChatResponse parsed = GSON.fromJson(response.body(), ChatResponse.class);
                        if (parsed == null) {
                            throw new CoachApiException("백엔드 응답이 비어 있어요.");
                        }
                        return parsed;
                    } catch (JsonSyntaxException e) {
                        throw new CoachApiException("백엔드 응답을 해석하지 못했어요.", e);
                    }
                });
    }

    /**
     * 코치에게 메시지를 보내고 SSE로 응답을 토큰 단위로 받는다(코치 창 전용).
     *
     * <p>콜백은 HTTP 스레드에서 호출되므로, 화면 갱신을 하려면 호출자가 게임(클라이언트)
     * 스레드로 옮겨야 한다.
     *
     * @param onToken    토큰 조각이 도착할 때마다 호출 (점진적 표시용)
     * @param onComplete 완료 시 최종 응답(answer·todos·recipe 포함)으로 호출
     * @param onError    연결·응답 오류 시 호출
     */
    public static void chatStream(String message,
                                  List<InventorySnapshot.InventoryItem> inventory,
                                  GameStateSnapshot.GameState gameState,
                                  Consumer<String> onToken,
                                  Consumer<ChatResponse> onComplete,
                                  Consumer<Throwable> onError) {
        final String url = CoachConfig.backendUrl() + "/api/v1/chat";
        final String payload = GSON.toJson(new ChatRequest(message, CoachConfig.threadId(), inventory, gameState));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(120))
                .header("Content-Type", "application/json")
                .header("Accept", "text/event-stream")
                .POST(HttpRequest.BodyPublishers.ofString(payload, StandardCharsets.UTF_8))
                .build();

        HTTP.sendAsync(request, HttpResponse.BodyHandlers.ofLines())
                .thenAccept(response -> {
                    int status = response.statusCode();
                    if (status / 100 != 2) {
                        onError.accept(new CoachApiException("백엔드 응답 오류 (HTTP " + status + ")"));
                        return;
                    }
                    boolean[] completed = {false};
                    try (Stream<String> lines = response.body()) {
                        lines.forEach(line -> handleSseLine(line, onToken, onComplete, completed));
                    }
                    if (!completed[0]) {
                        // done 이벤트 없이 스트림이 끝났으면 빈 응답으로 마무리해 UI가 멈추지 않게 한다.
                        onComplete.accept(new ChatResponse());
                    }
                })
                .exceptionally(error -> {
                    onError.accept(new CoachApiException(
                            "백엔드에 연결하지 못했어요. 서버가 켜져 있는지 확인해 주세요 (" + url + ")", error));
                    return null;
                });
    }

    /** SSE 한 줄(`data: {json}`)을 파싱해 토큰/완료 콜백으로 분배한다. */
    private static void handleSseLine(String line, Consumer<String> onToken,
                                      Consumer<ChatResponse> onComplete, boolean[] completed) {
        if (line == null || !line.startsWith("data:")) {
            return; // 이벤트 사이 빈 줄 등은 무시
        }
        String json = line.substring("data:".length()).trim();
        if (json.isEmpty()) {
            return;
        }
        StreamEvent ev;
        try {
            ev = GSON.fromJson(json, StreamEvent.class);
        } catch (JsonSyntaxException e) {
            return; // 한 이벤트 파싱 실패는 건너뛴다
        }
        if (ev == null || ev.event == null) {
            return;
        }
        if ("token".equals(ev.event)) {
            if (ev.data != null && !ev.data.isEmpty()) {
                onToken.accept(ev.data);
            }
        } else if ("done".equals(ev.event)) {
            ChatResponse done = null;
            try {
                done = GSON.fromJson(ev.data, ChatResponse.class);
            } catch (JsonSyntaxException ignored) {
                // 파싱 실패 시 빈 응답으로 마무리
            }
            completed[0] = true;
            onComplete.accept(done != null ? done : new ChatResponse());
        }
        // "node" 등 그 외 이벤트는 모드가 사용하지 않는다.
    }
}
