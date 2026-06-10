from typing import TypedDict

class IngredientState(TypedDict):
    image_path: str

    global_ingredients: list[str]
    window_ingredients: list[str]

    final_ingredients: list[str]