package com.enderdragon.coach.gui;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.util.List;

public class TodoScreen extends Screen {

    private static final int PANEL_WIDTH = 260;
    private static final int PANEL_TOP = 40;
    private static final int LINE_HEIGHT = 14;
    private static final int PADDING = 8;

    private static final int BG_COLOR        = 0xC0000000;
    private static final int SELECTED_BG     = 0x60FFAA00;
    private static final int TEXT_COLOR      = 0xFFEEEEEE;
    private static final int SELECTED_COLOR  = 0xFFFFDD44;
    private static final int COMPLETE_COLOR  = 0xFFFF8844;
    private static final int TITLE_COLOR     = 0xFFFFAA00;
    private static final int HINT_COLOR      = 0xFF888888;
    private static final int SEPARATOR_COLOR = 0x60FFFFFF;

    private static final int CELEBRATION_TICKS = 25;

    // sparkle 문자와 8방향 단위벡터
    private static final String[] SPARKLES = {"*", "+", "o", ".", "*", "+", ".", "o"};
    private static final int[][] DIRS = {
        { 0, -1}, { 1, -1}, { 1,  0}, { 1,  1},
        { 0,  1}, {-1,  1}, {-1,  0}, {-1, -1}
    };

    private int selectedIndex = 0;
    private int celebrationTicks = 0;
    private boolean completingAll = false;

    public TodoScreen() {
        super(Text.literal("할 일 목록"));
    }

    // 선택 가능한 항목 수 = TODO 수 + "모두 완료" 1개
    private int totalCount() {
        return TodoList.items().size() + 1;
    }

    // ── tick: 애니메이션 카운트다운 및 완료 처리 ──────────────────────────

    @Override
    public void tick() {
        if (celebrationTicks <= 0) return;
        celebrationTicks--;
        if (celebrationTicks == 0) {
            if (completingAll) {
                TodoList.completeAll();
                this.close();
            } else {
                TodoList.complete(selectedIndex);
                if (TodoList.isEmpty()) {
                    this.close();
                } else {
                    selectedIndex = Math.min(selectedIndex, TodoList.items().size());
                }
            }
        }
    }

    // ── 키 입력 처리 ─────────────────────────────────────────────────────

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (celebrationTicks > 0) return true; // 애니메이션 중 입력 차단

        int total = totalCount();
        switch (keyCode) {
            case GLFW.GLFW_KEY_UP -> {
                selectedIndex = (selectedIndex - 1 + total) % total;
                return true;
            }
            case GLFW.GLFW_KEY_DOWN -> {
                selectedIndex = (selectedIndex + 1) % total;
                return true;
            }
            case GLFW.GLFW_KEY_ENTER, GLFW.GLFW_KEY_KP_ENTER -> {
                startCelebration();
                return true;
            }
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    private void startCelebration() {
        MinecraftClient mc = MinecraftClient.getInstance();
        completingAll = (selectedIndex == TodoList.items().size());
        celebrationTicks = CELEBRATION_TICKS;

        if (mc.player != null) {
            if (completingAll) {
                mc.player.playSound(SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, 0.5f, 1.0f);
            } else {
                mc.player.playSound(SoundEvents.ENTITY_EXPERIENCE_ORB_PICKUP, 1.0f, 1.3f);
            }
        }
    }

    // ── 렌더링 ────────────────────────────────────────────────────────────

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        List<TodoList.TodoItem> items = TodoList.items();

        int panelX = (this.width - PANEL_WIDTH) / 2;
        int panelY = PANEL_TOP;
        // 패널 높이: 제목 + TODO 항목들 + 구분선 + 모두 완료 + 조작 힌트
        int panelH = PADDING + LINE_HEIGHT               // 제목
                   + items.size() * LINE_HEIGHT          // TODO 항목
                   + 6                                   // 구분선 여백
                   + LINE_HEIGHT                         // 모두 완료
                   + LINE_HEIGHT + PADDING;              // 조작 힌트

        // 패널 배경
        context.fill(panelX - PADDING, panelY - PADDING,
                     panelX + PANEL_WIDTH + PADDING, panelY + panelH, BG_COLOR);

        // 제목
        context.drawText(textRenderer, "[ 할 일 목록 ]", panelX, panelY, TITLE_COLOR, true);

        int y = panelY + LINE_HEIGHT + PADDING / 2;

        // TODO 항목 렌더링
        for (int i = 0; i < items.size(); i++) {
            boolean isSelected  = (selectedIndex == i) && celebrationTicks == 0;
            boolean celebrating = (selectedIndex == i) && celebrationTicks > 0 && !completingAll;

            if (isSelected) {
                context.fill(panelX - 2, y - 1, panelX + PANEL_WIDTH + 2, y + LINE_HEIGHT - 1, SELECTED_BG);
            }

            String text = (isSelected ? "> " : "  ") + (i + 1) + ". " + items.get(i).fullText;
            int color = celebrating ? 0xFFFFFF44 : (isSelected ? SELECTED_COLOR : TEXT_COLOR);
            context.drawText(textRenderer, text, panelX + 2, y + 1, color, false);

            if (celebrating) {
                renderSparkles(context, panelX + 2, y + 1);
            }

            y += LINE_HEIGHT;
        }

        // 구분선
        y += 3;
        context.fill(panelX, y, panelX + PANEL_WIDTH, y + 1, SEPARATOR_COLOR);
        y += 5;

        // 모두 완료 항목
        boolean allSelected  = (selectedIndex == items.size()) && celebrationTicks == 0;
        boolean allCelebrate = completingAll && celebrationTicks > 0;

        if (allSelected) {
            context.fill(panelX - 2, y - 1, panelX + PANEL_WIDTH + 2, y + LINE_HEIGHT - 1, SELECTED_BG);
        }
        String allText  = (allSelected ? "> " : "  ") + "[ 모두 완료 ]";
        int    allColor = allCelebrate ? 0xFFFFFF44 : (allSelected ? SELECTED_COLOR : COMPLETE_COLOR);
        context.drawText(textRenderer, allText, panelX + 2, y + 1, allColor, false);
        if (allCelebrate) {
            renderSparkles(context, panelX + 2, y + 1);
        }

        y += LINE_HEIGHT + PADDING / 2;

        // 조작 힌트
        context.drawText(textRenderer, "[ 위/아래 ] 선택   [ Enter ] 완료   [ Esc ] 닫기",
                         panelX, y, HINT_COLOR, false);

        // 축하 메시지 (애니메이션 중)
        if (celebrationTicks > 0) {
            renderCelebrationBanner(context, panelY + panelH + 6);
        }
    }

    private void renderSparkles(DrawContext context, int itemX, int itemY) {
        int progress = CELEBRATION_TICKS - celebrationTicks; // 0(시작) → 25(종료)
        int spread   = progress * 3;
        int alpha    = (int)(255 * celebrationTicks / (float) CELEBRATION_TICKS);
        int baseRgb  = 0x00FFAA00; // ARGB에서 alpha 제외한 gold RGB

        for (int i = 0; i < SPARKLES.length; i++) {
            int sx = itemX + DIRS[i][0] * spread;
            int sy = itemY + DIRS[i][1] * spread;
            int color = (alpha << 24) | baseRgb;
            context.drawText(textRenderer, SPARKLES[i], sx, sy, color, false);
        }
    }

    private void renderCelebrationBanner(DrawContext context, int bannerY) {
        String msg = completingAll ? ">> 모두 완료! <<" : ">> 완료! <<";
        int alpha  = (int)(220 * celebrationTicks / (float) CELEBRATION_TICKS);
        int color  = (alpha << 24) | 0x00FFDD00;
        int msgX   = this.width / 2 - textRenderer.getWidth(msg) / 2;
        context.drawText(textRenderer, msg, msgX, bannerY, color, true);
    }

    @Override
    public boolean shouldPause() {
        return false;
    }
}
