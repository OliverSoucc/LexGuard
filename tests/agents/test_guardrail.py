import sys
import types
from types import SimpleNamespace

fake_langchain_openai = types.ModuleType("langchain_openai")
fake_langchain_core_prompts = types.ModuleType("langchain_core.prompts")

class FakeChain:
    def invoke(self, payload):
        return SimpleNamespace(is_safe=True, reason="")

class FakeChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass
    def with_structured_output(self, schema, **kwargs):
        return self

class FakeChatPromptTemplate:
    @classmethod
    def from_messages(cls, messages):
        return cls()
    def __or__(self, other):
        return FakeChain()

fake_langchain_openai.ChatOpenAI = FakeChatOpenAI
fake_langchain_core_prompts.ChatPromptTemplate = FakeChatPromptTemplate

sys.modules["langchain_openai"] = fake_langchain_openai
sys.modules["langchain_core.prompts"] = fake_langchain_core_prompts


from src.agents.guardrail import guardrail_node


def test_guardrail_returns_block_when_chain_marks_unsafe(base_state):
    original_chain = guardrail_node.chain
    guardrail_node.chain = SimpleNamespace(
        invoke=lambda _: SimpleNamespace(
            is_safe=False,
            critique="Prompt injection detected."
        )
    )

    try:
        result = guardrail_node(base_state)
        assert result["is_safe"] is False
        assert "Security Guardrail Block" in result["draft_answer"]
        assert "Prompt injection detected." in result["draft_answer"]
    finally:
        guardrail_node.chain = original_chain


def test_guardrail_returns_safe_when_chain_marks_safe(base_state):
    original_chain = guardrail_node.chain
    guardrail_node.chain = SimpleNamespace(
        invoke=lambda _: SimpleNamespace(
            is_safe=True,
            critique=""
        )
    )

    try:
        result = guardrail_node(base_state)
        assert result["is_safe"] is True
        assert "draft_answer" not in result
        assert "context" not in result

    finally:
        guardrail_node.chain = original_chain