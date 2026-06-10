from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END

from app.graph.state import IngredientState

from app.agents.global_agent import global_agent
from app.agents.window_agent import window_agent
from app.agents.fusion_agent import fusion_agent

builder = StateGraph(
    IngredientState
)

builder.add_node(
    "global_agent",
    global_agent
)

builder.add_node(
    "window_agent",
    window_agent
)

builder.add_node(
    "fusion_agent",
    fusion_agent
)

builder.add_edge(
    START,
    "global_agent"
)

builder.add_edge(
    START,
    "window_agent"
)

builder.add_edge(
    "global_agent",
    "fusion_agent"
)

builder.add_edge(
    "window_agent",
    "fusion_agent"
)

builder.add_edge(
    "fusion_agent",
    END
)

graph = builder.compile()