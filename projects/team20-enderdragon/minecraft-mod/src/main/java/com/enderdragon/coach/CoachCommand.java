package com.enderdragon.coach;

import com.enderdragon.coach.api.ChatResponse;
import com.enderdragon.coach.api.CoachApiClient;
import com.enderdragon.coach.api.InventorySnapshot;
import com.enderdragon.coach.gui.TodoList;
import com.mojang.brigadier.Command;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandManager;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletionException;

/**
 * 클라이언트 채팅 명령어 {@code /coach <메시지>}.
 *
 * <p>입력을 백엔드 코칭 API로 보내고, 비동기 응답을 받아 채팅창에 출력한다.
 * 네트워크 호출은 백그라운드에서 일어나고, 채팅 출력은 항상 클라이언트(게임) 스레드에서 한다.
 */
public final class CoachCommand {

    private CoachCommand() {
    }

    /** 클라이언트 명령어 등록 콜백에 {@code /coach}를 등록한다. */
    public static void register() {
        ClientCommandRegistrationCallback.EVENT.register((dispatcher, registryAccess) ->
                dispatcher.register(ClientCommandManager.literal("coach")
                        .then(ClientCommandManager.argument("message", StringArgumentType.greedyString())
                                .executes(context -> {
                                    ask(StringArgumentType.getString(context, "message"));
                                    return Command.SINGLE_SUCCESS;
                                }))
                        .executes(context -> {
                            printLine(Text.literal("사용법: /coach <질문>   예) /coach 이제 뭐 해야 해?")
                                    .formatted(Formatting.YELLOW));
                            return Command.SINGLE_SUCCESS;
                        })));
    }

    private static void ask(String message) {
        printLine(Text.literal("[코치] 물어보는 중…").formatted(Formatting.GRAY));

        MinecraftClient mc = MinecraftClient.getInstance();
        List<InventorySnapshot.InventoryItem> inv = (mc.player != null)
                ? InventorySnapshot.capture(mc.player.getInventory())
                : Collections.emptyList();

        CoachApiClient.chat(message, inv).whenComplete((response, error) -> {
            MinecraftClient client = MinecraftClient.getInstance();
            client.execute(() -> {
                if (error != null) {
                    printLine(Text.literal("[코치] " + describe(error)).formatted(Formatting.RED));
                    return;
                }
                printAnswer(response);
            });
        });
    }

    /** 코치 답변을 줄 단위로 나눠 채팅에 출력하고 할 일 목록을 갱신한다. */
    private static void printAnswer(ChatResponse response) {
        String answer = response.answerOrEmpty();
        if (answer.isBlank()) {
            printLine(Text.literal("[코치] 답변이 비어 있어요. 다시 물어봐 주세요.").formatted(Formatting.RED));
            return;
        }
        // 할 일 목록: 백엔드가 만든 짧은 todos 우선, 없으면 answer 파싱으로 폴백
        if (response.hasTodos()) {
            TodoList.addAll(response.todos);
        } else {
            TodoList.parseAndAdd(answer);
        }
        printLine(Text.literal("[코치]").formatted(Formatting.GREEN, Formatting.BOLD));
        for (String line : answer.split("\\r?\\n")) {
            printLine(Text.literal(line));
        }
    }

    private static String describe(Throwable error) {
        Throwable cause = (error instanceof CompletionException && error.getCause() != null)
                ? error.getCause() : error;
        return cause.getMessage() != null ? cause.getMessage() : "알 수 없는 오류가 발생했어요.";
    }

    /** 클라이언트 측에만 보이는 채팅 메시지를 출력한다(서버로 전송되지 않음). */
    private static void printLine(Text text) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client.player != null) {
            client.player.sendMessage(text, false);
        } else if (client.inGameHud != null) {
            client.inGameHud.getChatHud().addMessage(text);
        }
    }
}
