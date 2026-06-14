import os

from langgraph.graph import StateGraph, END

from src.utils.helpers import route_by_guardrail, route_by_auditor
from src.utils.visualization import save_graph_png

from src.agents.guardrail import guardrail_node
from src.agents.state import GraphState
from src.agents.researcher import researcher_node
from src.agents.auditor import auditor_node

def build_lexguard_app():
    workflow = StateGraph(GraphState)

    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("auditor", auditor_node)

    workflow.set_entry_point("guardrail")

    workflow.add_conditional_edges(
        "guardrail",
        route_by_guardrail,
        {"researcher": "researcher", "end": END}
    )

    workflow.add_edge("researcher", "auditor")

    workflow.add_conditional_edges(
        "auditor",
        route_by_auditor,
        {"end": END, "researcher": "researcher"}
    )

    return workflow.compile()


lexguard_app = build_lexguard_app()

if os.getenv("LEXGUARD_DRAW_GRAPH") == "1":
    save_graph_png(lexguard_app)



