import os
import json
import time
import shutil
import torch
from typing import List

import mlflow
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.config import (
    INTERIM_DATA_DIR,
    VECTORSTORE_DIR,
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_METRICS_PATH,
    MLFLOW_TRACKING_URI,
    EXPERIMENT_DATA_PIPELINE,
)

os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_DATA_PIPELINE)


def load_interim_documents() -> List[Document]:
    path = INTERIM_DATA_DIR

    if not path.exists():
        raise FileNotFoundError(f"❌ Directory not found: {path}")

    files = sorted(path.glob("*.json"))
    print(f"📂 Found {len(files)} clean JSON documents.")

    documents = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_content = data.get("content", "")
            if not raw_content:
                print(f"⚠️ Skipping empty file: {file_path.name}")
                continue

            metadata = data.get("metadata", {})
            metadata["source"] = data.get("source", file_path.name)

            documents.append(
                Document(
                    page_content=raw_content,
                    metadata=metadata,
                )
            )

        except Exception as e:
            print(f"⚠️ Failed to load {file_path.name}: {e}")

    return documents


def run_ingestion():
    start_time = time.time()

    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"

    print(f"🚀 RUNNING ON: {device.upper()}")

    print("📖 Loading interim data...")
    docs = load_interim_documents()
    if not docs:
        print("❌ No documents loaded. Stopping.")
        return
    print(f"✅ Loaded {len(docs)} documents.")

    print("✂️ Splitting text...")
    forensic_separators = [
        "\n# ", "\n## ", "\n### ",
        "\n ## ", "\n*ANNEX",
        "\n*Čl.", "\n*§", "\n*PRVÁ ČASŤ", "\n*K Čl.",
        "\n➢",
        "\n*Article", "\nArticle ", "\nČlánok ", "\n§ ",
        "\n\n", "\n", " "
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=forensic_separators,
    )

    raw_chunks = text_splitter.split_documents(docs)

    final_processed_chunks = []
    for chunk in raw_chunks:
        if not chunk.page_content.startswith("passage: "):
            chunk.page_content = f"passage: {chunk.page_content}"
        final_processed_chunks.append(chunk)

    total_chunks = len(final_processed_chunks)
    print(f"🧱 Generated {total_chunks} chunks successfully prefixed for E5 vector alignment.")

    print(f"🧠 Loading Model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": device},
        show_progress=True,
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 16
        }
    )

    if VECTORSTORE_DIR.exists():
        print("MOP 🧹 [Cleanup] Deleting old vectorstore directory to ensure a clean overwrite...")
        shutil.rmtree(VECTORSTORE_DIR)

    print("🚀 STARTING EMBEDDING (Indexing structured matrices to Chroma)...")

    Chroma.from_documents(
        documents=final_processed_chunks,
        embedding=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )

    end_time = time.time()
    duration = end_time - start_time
    print(f"✨ SUCCESS: Vector DB saved to {VECTORSTORE_DIR} in {duration:.2f} seconds.")

    metrics_payload = {
        "model": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "overlap": CHUNK_OVERLAP,
        "device": device,
        "source_format": "JSON/Markdown",
        "total_chunks": total_chunks,
        "execution_time_seconds": round(duration, 2)
    }

    with open(EMBEDDING_METRICS_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=4)
    print(f"✅ Metrics sidecar saved to {EMBEDDING_METRICS_PATH}")

    print("📊 Logging ingestion data pipeline parameters and metrics straight to MLflow...")
    try:
        with mlflow.start_run(run_name="Legal-Ingestion-Final"):
            mlflow.log_params({
                "model": metrics_payload["model"],
                "chunk_size": metrics_payload["chunk_size"],
                "overlap": metrics_payload["overlap"],
                "device": metrics_payload["device"],
                "source_format": metrics_payload["source_format"]
            })
            mlflow.log_metric("total_chunks", metrics_payload["total_chunks"])
            mlflow.log_metric("execution_time_seconds", metrics_payload["execution_time_seconds"])
        print("✅ Successfully synchronized run telemetry with MLflow Server!")
    except Exception as e:
        print(f"⚠️ MLflow logging failed (Check server connection or network routes): {e}")


if __name__ == "__main__":
    run_ingestion()