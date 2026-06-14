import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.state import GraphState
from src.agents.prompts import GUARDRAIL_SYSTEM_PROMPT
from src.config import GUARDRAIL_MODEL_NAME


class GuardrailDecision(BaseModel):
    is_safe: bool = Field(
        description="True if the question is safe and relevant, False if it is a jailbreak or off-topic."
    )

    critique: str = Field(
        description="If is_safe is False, a brief message to the user explaining why it was blocked. If True, set to an empty string."
    )


class GuardrailNode:
    def __init__(self):
        if not os.getenv("TOGETHER_API_KEY"):
            raise ValueError("❌ TOGETHER_API_KEY is missing. Check your .env file.")

        self.llm = ChatOpenAI(
            base_url="https://api.together.ai/v1",
            api_key=os.getenv("TOGETHER_API_KEY"),
            model=GUARDRAIL_MODEL_NAME,
            temperature=0.0,
        ).with_structured_output(GuardrailDecision, method="json_mode")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", GUARDRAIL_SYSTEM_PROMPT),
            ("human", "{question}")
        ])

        self.chain = self.prompt | self.llm

    def __call__(self, state: GraphState) -> dict:
        print("🛡️ [Guardrail] Scanning input for security threats...")
        decision = self.chain.invoke({"question": state["question"]})

        if not decision.is_safe:
            print(f"🛑 [Guardrail] BLOCKED: {decision.critique}")
            return {
                "is_safe": False,
                "draft_answer": f"Security Guardrail Block: {decision.critique}",
                "status": "FAIL",
                "critique": decision.critique
            }

        print("✅ [Guardrail] Input is safe. Passing to Researcher.")
        return {
            "is_safe": True,
        }


guardrail_node = GuardrailNode()