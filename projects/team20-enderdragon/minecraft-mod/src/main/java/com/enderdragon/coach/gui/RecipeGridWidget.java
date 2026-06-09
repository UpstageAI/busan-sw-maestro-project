package com.enderdragon.coach.gui;

import com.enderdragon.coach.api.ChatResponse;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

/**
 * 코치 응답의 3×3 제작법 격자를 아이콘으로 렌더링하는 위젯.
 *
 * <p>백엔드가 보낸 아이템 ID 격자(9칸)를 {@link ItemStack}으로 변환해, 작업대처럼
 * 3×3 슬롯 + 화살표 + 결과 슬롯으로 그린다. 텍스처는 게임의 아이템 렌더러를 그대로
 * 쓰므로 별도 애셋이 필요 없고, 슬롯에 마우스를 올리면 아이템 이름 툴팁이 뜬다.
 */
public final class RecipeGridWidget {

    private static final int SLOT = 18;          // 슬롯 한 변(px)
    private static final int ICON_INSET = 1;     // 슬롯 안 아이콘 여백
    private static final int ARROW_GAP = 6;      // 격자–화살표–결과 간격
    private static final int CAPTION_H = 11;     // 캡션 줄 높이
    private static final int PAD = 4;            // 패널 안쪽 여백

    private static final int SLOT_BG = 0xFF8B8B8B;
    private static final int SLOT_BORDER = 0xFF373737;
    private static final int PANEL_BG = 0xC01A1A1A;
    private static final int CAPTION_COLOR = 0xFFE0E0E0;

    private final ItemStack[] cells = new ItemStack[9]; // 빈 칸은 null
    private ItemStack output = ItemStack.EMPTY;
    private boolean present = false;

    /** 백엔드 격자를 ItemStack으로 변환해 보관한다(없거나 비면 숨김 상태). */
    public void set(ChatResponse.Recipe recipe) {
        present = false;
        for (int i = 0; i < 9; i++) {
            cells[i] = null;
        }
        output = ItemStack.EMPTY;
        if (recipe == null || recipe.grid == null) {
            return;
        }
        int n = Math.min(9, recipe.grid.size());
        for (int i = 0; i < n; i++) {
            cells[i] = toStack(recipe.grid.get(i), 1);
        }
        ItemStack out = toStack(recipe.output, Math.max(1, recipe.count));
        if (out != null) {
            output = out;
            present = true;
        }
    }

    public boolean isPresent() {
        return present;
    }

    /** 캡션 + 격자를 포함한 패널 전체 높이(px). 없으면 0. */
    public int panelHeight() {
        return present ? PAD + CAPTION_H + SLOT * 3 + PAD : 0;
    }

    /**
     * 패널 배경 + 캡션 + 3×3 격자 + 결과 슬롯을 그린다. 슬롯 호버 시 아이템 툴팁도 그린다.
     *
     * @param x,y        패널 좌상단
     * @param panelWidth 패널 가로 폭
     */
    public void render(DrawContext ctx, TextRenderer tr, int x, int y, int panelWidth, int mouseX, int mouseY) {
        if (!present) {
            return;
        }
        ctx.fill(x, y, x + panelWidth, y + panelHeight(), PANEL_BG);

        // 캡션: "제작법 — <결과물 이름> ×개수"
        String count = output.getCount() > 1 ? " ×" + output.getCount() : "";
        Text caption = Text.literal("제작법 — ").append(output.getName()).append(Text.literal(count));
        ctx.drawText(tr, caption, x + PAD, y + PAD, CAPTION_COLOR, false);

        int gridX = x + PAD;
        int gridY = y + PAD + CAPTION_H;
        ItemStack hovered = null;

        // 3×3 격자
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 3; col++) {
                int sx = gridX + col * SLOT;
                int sy = gridY + row * SLOT;
                drawSlot(ctx, sx, sy);
                ItemStack stack = cells[row * 3 + col];
                if (stack != null) {
                    ctx.drawItem(stack, sx + ICON_INSET, sy + ICON_INSET);
                    if (isOver(mouseX, mouseY, sx, sy)) {
                        hovered = stack;
                    }
                }
            }
        }

        // 화살표 + 결과 슬롯(가운데 줄 높이에 맞춤)
        int arrowX = gridX + SLOT * 3 + ARROW_GAP;
        int midY = gridY + SLOT + (SLOT - tr.fontHeight) / 2;
        ctx.drawText(tr, Text.literal("→"), arrowX, midY, 0xFFFFFFFF, false);

        int outX = arrowX + tr.getWidth("→") + ARROW_GAP;
        int outY = gridY + SLOT;
        drawSlot(ctx, outX, outY);
        ctx.drawItem(output, outX + ICON_INSET, outY + ICON_INSET);
        ctx.drawItemInSlot(tr, output, outX + ICON_INSET, outY + ICON_INSET); // 개수 오버레이
        if (isOver(mouseX, mouseY, outX, outY)) {
            hovered = output;
        }

        // 툴팁은 다른 요소 위에 그려야 하므로 마지막에
        if (hovered != null) {
            ctx.drawItemTooltip(tr, hovered, mouseX, mouseY);
        }
    }

    private static void drawSlot(DrawContext ctx, int x, int y) {
        ctx.fill(x, y, x + SLOT, y + SLOT, SLOT_BORDER);          // 테두리
        ctx.fill(x + 1, y + 1, x + SLOT - 1, y + SLOT - 1, SLOT_BG); // 안쪽
    }

    private static boolean isOver(int mouseX, int mouseY, int slotX, int slotY) {
        return mouseX >= slotX && mouseX < slotX + SLOT && mouseY >= slotY && mouseY < slotY + SLOT;
    }

    private static ItemStack toStack(String id, int count) {
        if (id == null || id.isBlank()) {
            return null;
        }
        Identifier ident = Identifier.tryParse(id);
        if (ident == null) {
            return null;
        }
        Item item = Registries.ITEM.get(ident);
        ItemStack stack = new ItemStack(item, count);
        return stack.isEmpty() ? null : stack; // 미등록 ID는 AIR → empty → null
    }
}
