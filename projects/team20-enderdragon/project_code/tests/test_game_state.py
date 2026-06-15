"""인게임 상태(game_state) 반영 테스트.

모드가 보낸 시간·체력 등이 프롬프트 블록으로 변환되고, 초기 상태에 실리는지 검증한다.
"""
from app.prompts.templates import format_game_state_block
from app.api import build_initial_state
from app.schemas import GameState, Position


def test_상태가_없으면_빈_블록():
    assert format_game_state_block({}) == ""


def test_밤과_낮은_체력_배고픔은_위험신호를_명시한다():
    block = format_game_state_block({
        "time_of_day": "night", "health": 4, "hunger": 3,
        "dimension": "minecraft:overworld", "position": {"x": 10, "y": 64, "z": -5},
    })
    assert "밤" in block
    assert "체력: 4/20" in block and "낮음" in block
    assert "배고픔: 3/20" in block
    assert "오버월드" in block
    assert "(10, 64, -5)" in block


def test_낮과_충분한_상태는_위험문구가_없다():
    block = format_game_state_block({"time_of_day": "day", "health": 20, "hunger": 20})
    assert "낮" in block
    assert "안전 확보 우선" not in block
    assert "음식 필요" not in block


def test_초기_상태에_game_state가_dict로_실린다():
    gs = GameState(time_of_day="night", health=18, hunger=10,
                   dimension="minecraft:overworld", position=Position(x=1, y=2, z=3))
    state = build_initial_state("이제 뭐 해?", game_state=gs)
    assert state["game_state"]["time_of_day"] == "night"
    assert state["game_state"]["position"]["y"] == 2


def test_game_state가_없으면_빈_dict():
    assert build_initial_state("안녕").get("game_state") == {}
