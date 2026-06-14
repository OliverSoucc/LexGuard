import pytest

@pytest.fixture
def base_state():
    return {
        "question": "What is Article 5?",
        "context": "",
        "draft_answer": "",
        "critique": "",
        "status": "",
        "retry_count": 0,
        "is_safe": True,
    }