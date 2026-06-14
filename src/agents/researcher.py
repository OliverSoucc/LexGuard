import os
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from src.agents.prompts import RESEARCHER_SYSTEM_PROMPT
from src.agents.state import GraphState

from src.config import (
    VECTORSTORE_DIR,
    EMBEDDING_MODEL_NAME,
    RETRIEVAL_TOP_K,
    RESEARCHER_MODEL_NAME,
)


class ResearcherNode:
    def __init__(self):
        if not os.getenv("TOGETHER_API_KEY"):
            raise ValueError("❌ TOGETHER_API_KEY is missing. Check your .env file.")

        self.persist_directory = VECTORSTORE_DIR

        self._vector_db = None
        self._retriever = None

        self.llm = ChatOpenAI(
            base_url="https://api.together.ai/v1",
            api_key=os.getenv("TOGETHER_API_KEY"),
            model=RESEARCHER_MODEL_NAME,
            temperature=0.1,
            max_tokens=1024
        )

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCHER_SYSTEM_PROMPT),
            ("human", "{question}")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    @property
    def vector_db(self):
        if self._vector_db is None:
            print("💾 [Initialization] Loading heavy Chroma Vector DB into memory...")
            device = "cuda" if torch.cuda.is_available() else "cpu"

            embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True}
            )

            self._vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings
            )
        return self._vector_db

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = self.vector_db.as_retriever(search_kwargs={"k": RETRIEVAL_TOP_K})
        return self._retriever

    def __call__(self, state: GraphState) -> dict:
        question = state["question"]
        critique = state.get("critique", "")
        retry_count = state.get("retry_count", 0)

        if retry_count == 0:
            print(f"🔍 [Researcher] Searching vector database for: '{question}'")
            formatted_query = f"query: {question}"

            docs = self.retriever.invoke(formatted_query)
            context = "\n\n".join(doc.page_content for doc in docs)
        else:
            print(f"✍️ [Researcher] Rewriting draft based on Auditor feedback (Try {retry_count})...")
            context = state["context"]

        draft_answer = self.chain.invoke({
            "question": question,
            "context": context,
            "critique": critique if critique else "No feedback yet. This is the first draft."
        })

        return {
            "context": context,
            "draft_answer": draft_answer
        }


researcher_node = ResearcherNode()