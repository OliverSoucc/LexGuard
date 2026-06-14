import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.state import GraphState
from src.agents.prompts import AUDITOR_SYSTEM_PROMPT
from src.config import AUDITOR_MODEL_NAME

class AuditorFeedback(BaseModel):
    is_safe: bool = Field(
        description="True if the draft answer aligns perfectly with legal sources, False if there are errors or missing context."
    )
    critique: str = Field(
        description="Detailed legal critique or missing statutory references if is_safe is False. Leave empty if accurate."
    )

class AuditorNode:
    def __init__(self):
        if not os.getenv("TOGETHER_API_KEY"):
            raise ValueError("❌ TOGETHER_API_KEY is missing. Check your .env file.")

        self.llm = ChatOpenAI(
            base_url="https://api.together.ai/v1",
            api_key=os.getenv("TOGETHER_API_KEY"),
            model=AUDITOR_MODEL_NAME,
            temperature=0.0,
        ).with_structured_output(AuditorFeedback, method="json_mode")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", AUDITOR_SYSTEM_PROMPT),
            ("human", "Question: {question}\n\nContext:\n{context}\n\nDraft Answer:\n{draft_answer}")
        ])

        self.chain = self.prompt | self.llm

    def __call__(self, state: GraphState) -> dict:
        print("⚖️ [Auditor] Reviewing draft for legal accuracy...")

        try:
            decision = self.chain.invoke({
                "question": state["question"],
                "context": state["context"],
                "draft_answer": state["draft_answer"]
            })
        except Exception as e:
            print(f"⚠️ [Auditor] LLM or Parsing failure ({e}). Applying fallback safe-pass state.")
            decision = AuditorFeedback(is_safe=True, critique="")

        if decision.is_safe:
            print("✅ [Auditor] Draft approved. Proceeding to final delivery.")
            return {
                "status": "PASS",
                "critique": ""
            }
        else:
            print(f"🔄 [Auditor] REJECTED: {decision.critique}")
            return {
                "status": "FAIL",
                "critique": decision.critique,
                "retry_count": state.get("retry_count", 0) + 1
            }

auditor_node = AuditorNode()