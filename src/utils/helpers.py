# LATER MOVE THIS SOMEWHERE ELSE SINCE THESE 2 ARE NOT GENERAL HELPER FUNCTIONS BUT
# ARE COUPLED WITH src.agents.graph, BUT MOVE HERE SO I WOULD BE ABLE TO TEST IT
from src.config import MAX_AUDITOR_RETRIES


def route_by_guardrail(state):
    if state["is_safe"] is False:
        return "end"

    return "researcher"


def route_by_auditor(state):
    if state["status"] == "PASS":
        return "end"

    if state["retry_count"] >= MAX_AUDITOR_RETRIES:
        print("⚠️ [System] Max retries reached. The agents cannot agree. Forcing exit.")
        return "end"

    return "researcher"