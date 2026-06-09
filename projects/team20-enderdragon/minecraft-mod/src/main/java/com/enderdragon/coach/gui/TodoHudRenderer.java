package com.enderdragon.coach.gui;

import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.render.RenderTickCounter;

import java.util.List;

public final class TodoHudRenderer {

    private static final int PADDING = 6;
    private static final int LINE_HEIGHT = 11;
    private static final int BG_COLOR   = 0x90000000;
    private static final int TITLE_COLOR = 0xFFFFAA00;
    private static final int TEXT_COLOR  = 0xFFEEEEEE;

    private TodoHudRenderer() {}

    public static void register() {
        HudRenderCallback.EVENT.register(TodoHudRenderer::render);
    }

    private static void render(DrawContext context, RenderTickCounter tickCounter) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc.options.hudHidden) return;
        if (mc.currentScreen instanceof TodoScreen) return;

        List<TodoList.TodoItem> items = TodoList.items();
        if (items.isEmpty()) return;

        int screenWidth = mc.getWindow().getScaledWidth();

        // 가장 긴 shortText 기준으로 패널 폭 계산
        int maxTextWidth = mc.textRenderer.getWidth("[ 할 일 ]");
        for (int i = 0; i < items.size(); i++) {
            int w = mc.textRenderer.getWidth((i + 1) + ". " + items.get(i).shortText);
            if (w > maxTextWidth) maxTextWidth = w;
        }

        int x = screenWidth - maxTextWidth - PADDING * 3;
        int y = PADDING;

        int bgHeight = PADDING + LINE_HEIGHT + items.size() * LINE_HEIGHT + PADDING;
        context.fill(x - PADDING, y, screenWidth - PADDING, y + bgHeight, BG_COLOR);

        context.drawText(mc.textRenderer, "[ 할 일 ]", x, y + PADDING, TITLE_COLOR, true);

        for (int i = 0; i < items.size(); i++) {
            String label = (i + 1) + ". " + items.get(i).shortText;
            context.drawText(mc.textRenderer, label, x, y + PADDING + (i + 1) * LINE_HEIGHT, TEXT_COLOR, false);
        }
    }
}
