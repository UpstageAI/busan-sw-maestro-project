package com.enderdragon.coach.gui;

import com.enderdragon.coach.api.CoachApiClient;
import com.enderdragon.coach.api.InventorySnapshot;
import com.enderdragon.coach.gui.TodoList;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.text.OrderedText;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletionException;

/**
 * 인게임 코치 전용 화면.
 *
 * <p>채팅 명령어(/coach)와 달리, 게임 채팅과 분리된 별도 창에서 대화 기록을 스크롤로 보고
 * 입력창·보내기 버튼으로 코치와 대화한다. 백엔드 호출은 {@link CoachApiClient}를 재사용한다.
 */
public class CoachScreen extends Screen {

    private static final int MARGIN = 20;
    private static final int LINE_HEIGHT = 11;
    private static final int INPUT_HEIGHT = 20;
    private static final int SEND_BUTTON_WIDTH = 50;

    private static final int COLOR_USER = 0xFFFFFFFF;
    private static final int COLOR_COACH = 0xFFA0E0A0;
    private static final int PANEL_BG = 0x90000000;

    private TextFieldWidget input;

    // 스크롤 상태
    private int scrollY = 0;
    private int maxScroll = 0;
    private boolean stickToBottom = true;

    public CoachScreen() {
        super(Text.literal("마크 코치"));
    }

    private int historyTop() {
        return MARGIN + 14;
    }

    private int historyBottom() {
        return this.height - MARGIN - INPUT_HEIGHT - 6;
    }

    private int panelTextWidth() {
        return this.width - MARGIN * 2 - 8;
    }

    @Override
    protected void init() {
        int inputY = this.height - MARGIN - INPUT_HEIGHT;
        int inputWidth = this.width - MARGIN * 2 - SEND_BUTTON_WIDTH - 4;

        input = new TextFieldWidget(this.textRenderer, MARGIN, inputY, inputWidth, INPUT_HEIGHT,
                Text.literal("메시지 입력"));
        input.setMaxLength(2000);
        input.setPlaceholder(Text.literal("메시지 입력…  (Enter로 전송)"));
        addDrawableChild(input);
        setInitialFocus(input);

        addDrawableChild(ButtonWidget.builder(Text.literal("보내기"), b -> send())
                .dimensions(this.width - MARGIN - SEND_BUTTON_WIDTH, inputY, SEND_BUTTON_WIDTH, INPUT_HEIGHT)
                .build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta); // 배경 흐림 + 위젯(입력창/버튼)

        // 제목
        context.drawText(this.textRenderer, this.title, MARGIN, MARGIN, 0xFFFFFFFF, false);

        int top = historyTop();
        int bottom = historyBottom();

        // 대화 기록 패널 배경
        context.fill(MARGIN, top, this.width - MARGIN, bottom, PANEL_BG);

        List<Line> lines = layoutLines();
        int viewHeight = bottom - top;
        int contentHeight = lines.size() * LINE_HEIGHT;
        maxScroll = Math.max(0, contentHeight - viewHeight);
        if (stickToBottom) {
            scrollY = maxScroll;
        }
        scrollY = clamp(scrollY, 0, maxScroll);

        context.enableScissor(MARGIN, top, this.width - MARGIN, bottom);
        int y = top + 2 - scrollY;
        for (Line line : lines) {
            if (y + LINE_HEIGHT >= top && y <= bottom) {
                context.drawText(this.textRenderer, line.text, MARGIN + 4, y, line.color, false);
            }
            y += LINE_HEIGHT;
        }
        context.disableScissor();

        if (lines.isEmpty()) {
            context.drawText(this.textRenderer,
                    Text.literal("코치에게 무엇이든 물어보세요. 예) 이제 뭐 해야 해?"),
                    MARGIN + 4, top + 4, 0xFF888888, false);
        }
    }

    /** 모든 메시지를 패널 너비에 맞춰 줄바꿈한 그리기 목록으로 변환한다. */
    private List<Line> layoutLines() {
        List<Line> result = new ArrayList<>();
        int width = panelTextWidth();
        for (CoachChatLog.Message m : CoachChatLog.messages()) {
            int color = m.fromUser ? COLOR_USER : COLOR_COACH;
            String prefix = m.fromUser ? "나: " : "코치: ";
            Text text = Text.literal(prefix + m.text);
            for (OrderedText ordered : this.textRenderer.wrapLines(text, width)) {
                result.add(new Line(ordered, color));
            }
        }
        return result;
    }

    private void send() {
        if (input == null) {
            return;
        }
        String message = input.getText().strip();
        if (message.isEmpty()) {
            return;
        }
        input.setText("");

        CoachChatLog.addUser(message);
        CoachChatLog.Message pending = CoachChatLog.addCoach("물어보는 중…");
        stickToBottom = true;

        MinecraftClient mc = MinecraftClient.getInstance();
        List<InventorySnapshot.InventoryItem> inv = (mc.player != null)
                ? InventorySnapshot.capture(mc.player.getInventory())
                : Collections.emptyList();

        CoachApiClient.chat(message, inv).whenComplete((response, error) ->
                MinecraftClient.getInstance().execute(() -> {
                    if (error != null) {
                        pending.text = "(오류) " + describe(error);
                    } else {
                        String answer = response.answerOrEmpty();
                        if (!answer.isBlank()) {
                            // 할 일 목록: 백엔드가 만든 짧은 todos 우선, 없으면 answer 파싱으로 폴백
                            if (response.hasTodos()) {
                                TodoList.addAll(response.todos);
                            } else {
                                TodoList.parseAndAdd(answer);
                            }
                        }
                        pending.text = answer.isBlank() ? "(빈 응답) 다시 물어봐 주세요." : answer;
                    }
                    stickToBottom = true;
                }));
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == GLFW.GLFW_KEY_ENTER || keyCode == GLFW.GLFW_KEY_KP_ENTER) {
            send();
            return true;
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double horizontalAmount, double verticalAmount) {
        scrollY = clamp(scrollY - (int) (verticalAmount * LINE_HEIGHT * 2), 0, maxScroll);
        stickToBottom = scrollY >= maxScroll;
        return true;
    }

    @Override
    public boolean shouldPause() {
        // 게임을 멈추지 않는다 — "게임 옆에 띄운 코치 창" 느낌.
        return false;
    }

    private static String describe(Throwable error) {
        Throwable cause = (error instanceof CompletionException && error.getCause() != null)
                ? error.getCause() : error;
        return cause.getMessage() != null ? cause.getMessage() : "알 수 없는 오류";
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private record Line(OrderedText text, int color) {
    }
}
