package com.enderdragon.coach.api;

import com.google.gson.annotations.SerializedName;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.world.ClientWorld;
import net.minecraft.util.math.BlockPos;

/**
 * 인게임 상태 스냅샷 — 시간대·체력·배고픔·차원·좌표.
 *
 * <p>인벤토리({@link InventorySnapshot})만으로는 다룰 수 없는 생존/상황 목표
 * ("밤 오는데 집 없어", "배고파")를 코치가 파악하도록 함께 전송한다.
 * 백엔드 스키마(app/schemas.py: GameState)와 필드명을 맞춘다.
 */
public final class GameStateSnapshot {

    /** 밤 판정 경계: 하루(24000틱) 중 13000~23000을 밤으로 본다. */
    private static final long NIGHT_START = 13000L;
    private static final long NIGHT_END = 23000L;

    public record Position(int x, int y, int z) {}

    public record GameState(
            @SerializedName("time_of_day") String timeOfDay,
            float health,
            int hunger,
            String dimension,
            Position position) {}

    private GameStateSnapshot() {}

    /** 현재 클라이언트 상태를 읽어 GameState로 반환한다. 플레이어/월드가 없으면 null. */
    public static GameState capture(MinecraftClient mc) {
        if (mc == null || mc.player == null || mc.world == null) return null;

        ClientPlayerEntity player = mc.player;
        ClientWorld world = mc.world;

        long timeOfDay = world.getTimeOfDay() % 24000L;
        String phase = (timeOfDay >= NIGHT_START && timeOfDay < NIGHT_END) ? "night" : "day";
        String dimension = world.getRegistryKey().getValue().toString();
        BlockPos pos = player.getBlockPos();

        return new GameState(
                phase,
                player.getHealth(),
                player.getHungerManager().getFoodLevel(),
                dimension,
                new Position(pos.getX(), pos.getY(), pos.getZ()));
    }
}
