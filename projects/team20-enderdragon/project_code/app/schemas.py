from uuid import uuid4
from typing import Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    thread_id: str                  # 세션 식별자 (진척도 load/persist에 사용)
    query: str
    history_text: str
    query_analysis: dict
    search_results: list[dict]
    structured_facts: list[str]
    final_answer: str
    domain: str
    need_clarification: bool        # 추가 - kje
    clarification_question: str     # 추가 - kje
    prev_was_clarification: bool    # 직전 턴이 되묻기였는지(무한 되묻기 방지)
    inventory: list[dict]           # 마크 Mod에서 전달한 인벤토리 (웹은 항상 [])
    inventory_connected: bool       # 인벤토리 연동 클라이언트(게임 모드) 여부 (웹은 False)
    game_state: dict                # 인게임 상태(시간·체력·좌표 등). 모드만 전달, 없으면 {}
    goal_class: str                 # 목표 클래스(craft|survival|explore|vague). resolve_goal 산출
    resolved_goal: str              # 해석·제안된 목표 문장(한국어). resolve_goal 산출
    goal_proposed: bool             # 막연한 질문에 코치가 목표를 제안했는지 (responder 프레이밍용)
    goal_key: str                   # 해석된 제작 목표 item id (없으면 "")
    material_plan: dict             # plan_materials 결과(부족 자원·채굴 티어). 제작 목표 있을 때만
    recipe: dict                    # 제작 목표의 3×3 격자(output·count·grid). shaped 목표 있을 때만
    prior_goal_key: str             # 직전 턴의 목표 item id (load_state가 로드)
    prior_last_inventory: list[dict]  # 직전 턴 종료 시 인벤토리 (진행 비교용)
    prior_plan: list[dict]          # 직전 턴의 plan 단계([{item, qty}]). load_state가 로드
    prior_completed: list[str]      # 현재 목표에서 누적 완료한 단계 item id. load_state가 로드
    progress_note: list[dict]       # 직전 턴 이후 새로 얻은 재료 (reconcile 산출)
    completed_steps: list[str]      # 이번 턴에 새로 완료된 plan 단계 item id (reconcile 산출)
    goal_completed: list[str]       # 현재 목표 누적 완료 단계(직전+이번). persist_state가 저장
    next_step: dict                 # 결정론으로 고른 다음 한 단계 (reconcile 산출)
    todos: list[str]                # 게임 할 일 목록용 짧은 명령형 TODO (게임 모드에서만 생성)

class QueryAnalysis(BaseModel):
    keywords: list[str] = Field(description="keywords")
    domain: Literal["minecraft","general","out_of_scope"] = Field(description="domain")
    intent: str = Field(description="intent")
    status: Literal["success","insufficient"] = Field(description="status")

class GoalResolution(BaseModel):
    """resolve_goal 노드의 구조화 출력 — 목표 클래스 분류 + (막연하면) 목표 제안."""
    goal_class: Literal["craft", "survival", "explore", "vague"] = Field(
        description="목표 성격: 제작/모으기=craft, 생존·안전·회복=survival, 탐험·이동=explore, 막연=vague"
    )
    goal_text: str = Field(default="", description="해석하거나 제안한 목표를 담은 한 문장(한국어)")
    proposed: bool = Field(
        default=False,
        description="사용자가 목표를 안 밝혀 상태를 근거로 코치가 제안한 경우 true",
    )


class ClarificationResult(BaseModel):
    need_clarification: bool = Field(description="추가 정보가 필요하면 true, 바로 답변 가능하면 false")
    question: str = Field(default="", description="need_clarification이 true일 때만 작성하는 한국어 되묻기 질문")

class TodoListResult(BaseModel):
    todos: list[str] = Field(
        default_factory=list,
        description="사용자가 수행할 행동만 담은 짧은 명령형 TODO 항목들 (예: '철 원석 3개 채굴', '화로 제작')",
    )

class InventoryItem(BaseModel):
    item: str
    count: int


class Position(BaseModel):
    x: int
    y: int
    z: int


class GameState(BaseModel):
    """인게임 상태 — 모드가 전송. 인벤토리만으로 모르는 생존/상황 파악에 쓴다."""
    time_of_day: str = ""           # "day" | "night"
    health: float = 0.0             # 0~20
    hunger: int = 0                 # 0~20
    dimension: str = ""             # "minecraft:overworld" 등
    position: Position | None = None


class SubgoalState(BaseModel):
    id: str
    title: str
    status: str = "pending"  # pending | active | done


class CoachingSnapshot(BaseModel):
    """세션별 코칭 진척도 스냅샷 (coaching_state.state에 JSON으로 저장).

    멀티턴에서 직전 계획 대비 진행을 비교(reconcile)하는 데 쓴다.
    """
    current_goal: str = ""
    goal_key: str = ""                                  # 정규화된 목표 키(예: minecraft:iron_pickaxe)
    plan: list[SubgoalState] = Field(default_factory=list)
    completed: list[str] = Field(default_factory=list)  # 완료한 subgoal id
    last_inventory: list[InventoryItem] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field(default_factory=lambda: str(uuid4()))
    inventory: list[InventoryItem] = Field(default_factory=list)
    # 게임 모드(인벤토리 연동 클라이언트)는 True. 웹은 필드를 보내지 않아 기본 False.
    inventory_connected: bool = Field(default=False)
    # 인게임 상태(시간·체력·좌표 등). 모드만 전송, 웹은 None.
    game_state: GameState | None = None

class RecipeGrid(BaseModel):
    """제작법 3×3 격자 — 모드 GUI가 아이콘으로 렌더링한다.

    grid는 9칸(행 우선, 좌상단 정렬)으로 각 칸은 아이템 ID 또는 빈 칸(null).
    """
    output: str                                          # 결과물 item id
    count: int = 1                                       # 결과 개수
    grid: list[str | None] = Field(default_factory=list)  # 9칸(item_id|null)


class ChatResponse(BaseModel):
    answer: str
    domain: str = ""
    sources: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    todos: list[str] = Field(default_factory=list)  # 게임 할 일 목록용 짧은 TODO (웹은 빈 배열)
    recipe: RecipeGrid | None = None                # 제작법 격자 (제작 목표가 있을 때만, 없으면 null)

class StreamEvent(BaseModel):
    event: str = "message"
    node: str = ""
    data: str = ""
