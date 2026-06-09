"""마인크래프트 확정 게임 사실 — 아이템 ID 번역·채굴 티어·제작/획득 레시피.

런타임에 바뀌지 않는 정적 참조 데이터. 출처: minecraft.wiki
"""

# Mod에서 전달되는 minecraft:item_id → 한국어명 매핑
ITEM_ID_TO_KO: dict[str, str] = {
    "minecraft:stick": "막대기",
    "minecraft:cobblestone": "조약돌",
    "minecraft:coal": "석탄",
    "minecraft:charcoal": "목탄",
    "minecraft:oak_log": "참나무 원목",
    "minecraft:oak_planks": "참나무 판자",
    "minecraft:birch_log": "자작나무 원목",
    "minecraft:birch_planks": "자작나무 판자",
    "minecraft:spruce_log": "가문비나무 원목",
    "minecraft:spruce_planks": "가문비나무 판자",
    "minecraft:jungle_log": "정글나무 원목",
    "minecraft:jungle_planks": "정글나무 판자",
    "minecraft:acacia_log": "아카시아나무 원목",
    "minecraft:acacia_planks": "아카시아나무 판자",
    "minecraft:dark_oak_log": "짙은 참나무 원목",
    "minecraft:dark_oak_planks": "짙은 참나무 판자",
    "minecraft:stone": "돌",
    "minecraft:iron_ore": "철광석",
    "minecraft:iron_ingot": "철 주괴",
    "minecraft:raw_iron": "철 원석",
    "minecraft:gold_ore": "금광석",
    "minecraft:gold_ingot": "금 주괴",
    "minecraft:diamond": "다이아몬드",
    "minecraft:diamond_ore": "다이아몬드 광석",
    "minecraft:coal_ore": "석탄 광석",
    "minecraft:crafting_table": "작업대",
    "minecraft:furnace": "화로",
    "minecraft:torch": "횃불",
    "minecraft:wooden_pickaxe": "나무 곡괭이",
    "minecraft:stone_pickaxe": "돌 곡괭이",
    "minecraft:iron_pickaxe": "철 곡괭이",
    "minecraft:golden_pickaxe": "금 곡괭이",
    "minecraft:diamond_pickaxe": "다이아몬드 곡괭이",
    "minecraft:wooden_sword": "나무 검",
    "minecraft:stone_sword": "돌 검",
    "minecraft:iron_sword": "철 검",
    "minecraft:golden_sword": "금 검",
    "minecraft:diamond_sword": "다이아몬드 검",
    "minecraft:wooden_axe": "나무 도끼",
    "minecraft:stone_axe": "돌 도끼",
    "minecraft:iron_axe": "철 도끼",
    "minecraft:diamond_axe": "다이아몬드 도끼",
    "minecraft:wooden_shovel": "나무 삽",
    "minecraft:stone_shovel": "돌 삽",
    "minecraft:iron_shovel": "철 삽",
    "minecraft:shears": "가위",
    "minecraft:wool": "양털",
    "minecraft:string": "실",
    "minecraft:bow": "활",
    "minecraft:arrow": "화살",
    "minecraft:feather": "깃털",
    "minecraft:flint": "부싯돌",
    "minecraft:flint_and_steel": "부싯돌과 강철",
    "minecraft:bucket": "양동이",
    "minecraft:water_bucket": "물 양동이",
    "minecraft:lava_bucket": "용암 양동이",
    "minecraft:leather": "가죽",
    "minecraft:beef": "소고기",
    "minecraft:cooked_beef": "구운 소고기",
    "minecraft:porkchop": "돼지고기",
    "minecraft:cooked_porkchop": "구운 돼지고기",
    "minecraft:chicken": "닭고기",
    "minecraft:cooked_chicken": "구운 닭고기",
    "minecraft:wheat": "밀",
    "minecraft:bread": "빵",
    "minecraft:apple": "사과",
    "minecraft:dirt": "흙",
    "minecraft:grass_block": "잔디 블록",
    "minecraft:sand": "모래",
    "minecraft:gravel": "자갈",
    "minecraft:netherrack": "네더랙",
    "minecraft:obsidian": "흑요석",
}


def item_ko(raw_id: str) -> str:
    """minecraft:item_id를 한국어명으로 변환한다.

    매핑에 없으면 네임스페이스(minecraft:)와 언더스코어만 정리해 폴백한다.
    빈 문자열이면 빈 문자열을 반환한다(기존 동작 유지).
    """
    return ITEM_ID_TO_KO.get(raw_id) or raw_id.replace("minecraft:", "").replace("_", " ")


# 곡괭이별 채굴 레벨 (★금 곡괭이는 0 = 나무와 동급, 철 이상 못 캠)
PICKAXE_LEVEL = {"나무": 0, "금": 0, "돌": 1, "철": 2, "다이아몬드": 3, "네더라이트": 4}

# 광물/블록 → 채굴에 필요한 최소 레벨
MINING_REQ = {
    "돌": 0,
    "석탄 광석": 0,
    "철광석": 1,
    "구리 광석": 1,
    "청금석 광석": 1,
    "금광석": 2,
    "레드스톤 광석": 2,
    "다이아몬드 광석": 2,
    "에메랄드 광석": 2,
    "흑요석": 3,
    "고대 잔해": 3,
}

# 채굴 레벨 → 사람이 읽는 사실 문구 (나무·금 제외를 명시해 환각 차단)
LEVEL_PHRASE = {
    0: "아무 곡괭이로 채굴 가능",
    1: "돌 곡괭이 이상 필요 (나무·금 곡괭이로는 못 캠)",
    2: "철 곡괭이 이상 필요 (금 곡괭이 제외)",
    3: "다이아몬드 또는 네더라이트 곡괭이 필요",
}

# 제작 레시피 (작업대 조합)
RECIPES = {
    "나무 곡괭이": "판자 3 + 막대기 2",
    "돌 곡괭이": "조약돌 3 + 막대기 2",
    "철 곡괭이": "철 주괴 3 + 막대기 2",
    "다이아몬드 곡괭이": "다이아몬드 3 + 막대기 2",
    "가위": "철 주괴 2",
    "침대": "양털 3개(같은 색) + 판자 3",
    "화로": "조약돌 8개 (또는 흑암·심층암 조약돌 등 '돌 등급' 블록 8개)",
    "작업대": "판자 4",
    "막대기": "판자 2",
    "횃불": "석탄 또는 목탄 1 + 막대기 1",
    "나무 검": "판자 2 + 막대기 1",
    "돌 검": "조약돌 2 + 막대기 1",
    "철 검": "철 주괴 2 + 막대기 1",
    "다이아몬드 검": "다이아몬드 2 + 막대기 1",
    "나무 도끼": "판자 3 + 막대기 2",
    "돌 도끼": "조약돌 3 + 막대기 2",
    "철 도끼": "철 주괴 3 + 막대기 2",
}

# 획득/가공 사실 (제작이 아니거나 경로가 헷갈리는 것)
ACQUIRE = {
    "철 주괴": (
        "주로 '철 원석(raw iron)'을 화로/용광로에 제련해 얻는다 "
        "(철광석을 캐면 철 원석이 떨어짐; 섬세한 손길로 캔 철광석 블록도 제련 가능). "
        "철 블록(→9개)·철 조각(9개→1)으로 제작도 가능."
    ),
    "다이아몬드": "다이아몬드 광석을 철 곡괭이 이상(금 곡괭이 제외)으로 채굴해 얻는다.",
}

# 검색어 정규화용 별칭 → 표준 키
ALIASES = {
    "철": "철광석",
    "철 광석": "철광석",
    "다이아": "다이아몬드 광석",
    "금": "금광석",
    "구리": "구리 광석",
    "레드스톤": "레드스톤 광석",
    "에메랄드": "에메랄드 광석",
    "석탄": "석탄 광석",
    "청금석": "청금석 광석",
}
