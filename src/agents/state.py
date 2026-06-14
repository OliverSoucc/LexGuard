from typing import TypedDict

class GraphState(TypedDict):
    context: str           # The raw legal text retrieved from ChromaDB     -> updates in researcher.py
    draft_answer: str      # The Researcher's proposed answer               -> updates in researcher.py
    retry_count: int       # Tracks how many times they have argued         -> updates in researcher.py
    status: str            # 'PASS' or 'FAIL' (Set by the Auditor)          -> updates in auditor.py
    critique: str          # The Auditor's feedback (if the draft fails)    -> updates in auditor.py
    is_safe:bool           # Tracks if the input passed the guardrail       -> updates in guardrail.py
    question: str          # The original question from the user            -> updates in main.py
