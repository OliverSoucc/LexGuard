from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


class QueryAgent:
    def __init__(self, model_name="intfloat/multilingual-e5-large"):
        """Initializes the embedding model and connects to the vector database."""

        ROOT = Path(__file__).resolve().parent.parent.parent
        self.persist_directory = str(ROOT / "data" / "vectorstore")

        if not (ROOT / "data" / "vectorstore").exists():
            print(f"❌ ERROR: Cannot find vectorstore at {self.persist_directory}")
            print("Did the rsync from the HPC fail?")
            return

        print(f"📂 Reading from: {self.persist_directory}")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={'normalize_embeddings': True}
        )

        self.vector_db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        print(f"✅ Database loaded. Total chunks: {self.vector_db._collection.count()}")

    def answer_question(self, query: str, k: int = 3):
        """Searches the database for the most relevant legal sections."""
        formatted_query = f"query: {query}"
        results = self.vector_db.similarity_search_with_score(formatted_query, k=k)
        return results


if __name__ == "__main__":
    agent = QueryAgent()

    # If the DB didn't load, stop here
    if not hasattr(agent, 'vector_db'):
        exit(1)

    test_queries = [
        "Aké sú hlavné povinnosti pre vysokorizikové systémy AI podľa slovenského návrhu?",
        "What are the criteria for general-purpose AI models with systemic risk?"
    ]

    for query in test_queries:
        results = agent.answer_question(query, k=3)

        print("-" * 50)
        print("📖 FOUND RELEVANT SECTIONS:")

        for i, (doc, score) in enumerate(results):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content[:300].replace('\n', ' ')
            print(f"\n--- Result {i + 1} | Score: {score:.4f} | Source: {source} ---")
            print(f"📄 {content_preview}...")