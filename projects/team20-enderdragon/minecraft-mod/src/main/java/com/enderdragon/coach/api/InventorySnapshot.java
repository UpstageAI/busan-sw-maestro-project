package com.enderdragon.coach.api;

import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class InventorySnapshot {

    public record InventoryItem(String item, int count) {}

    private InventorySnapshot() {}

    /**
     * 플레이어 인벤토리를 읽어 비어있지 않은 슬롯만 InventoryItem 리스트로 반환한다.
     * main(36) + armor(4) + offhand(1) 슬롯을 순회하며 빈 슬롯은 제외한다.
     */
    public static List<InventoryItem> capture(PlayerInventory inv) {
        if (inv == null) return Collections.emptyList();

        List<InventoryItem> result = new ArrayList<>();

        for (ItemStack stack : inv.main) {
            addIfPresent(result, stack);
        }
        for (ItemStack stack : inv.armor) {
            addIfPresent(result, stack);
        }
        for (ItemStack stack : inv.offHand) {
            addIfPresent(result, stack);
        }

        return result;
    }

    private static void addIfPresent(List<InventoryItem> result, ItemStack stack) {
        if (!stack.isEmpty()) {
            String id = Registries.ITEM.getId(stack.getItem()).toString();
            result.add(new InventoryItem(id, stack.getCount()));
        }
    }
}
