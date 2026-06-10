package com.enderdragon.coach;

import com.enderdragon.coach.gui.CoachScreen;
import com.enderdragon.coach.gui.TodoHudRenderer;
import com.enderdragon.coach.gui.TodoScreen;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import org.lwjgl.glfw.GLFW;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 클라이언트 진입점.
 *
 * <p>이 모드는 마인크래프트 인게임에서 백엔드 코칭 에이전트(FastAPI)를 호출하는
 * "연결(플러그인화) 기반"이다. 실제 코칭 로직은 백엔드에 있고, 모드는 입력을 받아
 * API를 호출하고 응답을 보여주는 얇은 클라이언트 역할만 한다.
 *
 * <p>진입점은 두 가지다 — 채팅 명령어 {@code /coach}와 전용 GUI 화면(기본 키 K).
 */
public class CoachClientMod implements ClientModInitializer {

    public static final String MOD_ID = "minecraft_coach";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static KeyBinding openCoachKey;
    private static KeyBinding openTodoKey;

    @Override
    public void onInitializeClient() {
        CoachCommand.register();
        TodoHudRenderer.register();
        registerCoachScreenKey();
        registerTodoScreenKey();
        LOGGER.info("[{}] 클라이언트 초기화 완료 — '/coach <메시지>' 또는 K 키로 코치, J 키로 할 일 목록을 호출하세요.", MOD_ID);
    }

    private void registerCoachScreenKey() {
        openCoachKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.minecraft_coach.open",
                InputUtil.Type.KEYSYM,
                GLFW.GLFW_KEY_K,
                "key.categories.minecraft_coach"));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (openCoachKey.wasPressed()) {
                client.setScreen(new CoachScreen());
            }
        });
    }

    private void registerTodoScreenKey() {
        openTodoKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.minecraft_coach.todo",
                InputUtil.Type.KEYSYM,
                GLFW.GLFW_KEY_J,
                "key.categories.minecraft_coach"));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (openTodoKey.wasPressed()) {
                client.setScreen(new TodoScreen());
            }
        });
    }
}
