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
     * @return 백엔드 응답을 담은 future. 실패 시 {@link CoachApiException}로 완료된다.
     */
    public static CompletableFuture<ChatResponse> chat(String message, List<InventorySnapshot.InventoryItem> inventory) {
        final String url = CoachConfig.backendUrl() + "/api/v1/chat/sync";
        final String payload = GSON.toJson(new ChatRequest(message, CoachConfig.threadId(), inventory));

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
}
