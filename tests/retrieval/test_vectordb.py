from types import SimpleNamespace
from src.ingestion.manual_debug_vectordb import QueryAgent


def test_query_agent_formats_query_and_returns_results():
    agent = QueryAgent.__new__(QueryAgent)

    captured = {}

    def fake_similarity_search_with_score(query, k):
        captured["query"] = query
        captured["k"] = k
        return [("doc1", 0.12), ("doc2", 0.21)]

    agent.vector_db = SimpleNamespace(
        similarity_search_with_score=fake_similarity_search_with_score
    )

    results = agent.answer_question("What is Article 5?", k=2)

    assert captured["query"] == "query: What is Article 5?"
    assert captured["k"] == 2
    assert len(results) == 2