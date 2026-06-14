# 🏛️ LegGuard: Multi-Agent AI Regulatory Compliance Pipeline

![Build Status](https://img.shields.io/badge/Dagger_Pipeline-Passing-brightgreen)
![Orchestration](https://img.shields.io/badge/Agents-LangGraph-orange)
![Telemetry](https://img.shields.io/badge/Tracking-MLflow-blue)
![Storage](https://img.shields.io/badge/DVC-Cloudflare_R2-yellow)

**LegGuard** is a Multi-Agent MLOps project designed to process, query, and evaluate high-stakes, bilingual (English and Slovak) legal and policy text concerning AI regulation within the European Union and the Slovak Republic. 

By leveraging **LangGraph** for resilient multi-agent orchestration, **Cloudflare R2** for efficient Data Version Control (DVC), and **Dagger** for containerized CI/CD, LegGuard provides a compliance-grade Retrieval-Augmented Generation (RAG) system capable of self-correction, rigorous citation, and strict security validation.

---

## 🏗️ Architecture Overview
* **Data Versioning (DVC):** Tracks compiled Chroma SQLite vector databases and interim JSON chunks, synced seamlessly to a Cloudflare R2 S3-compatible bucket.
* **Agent Orchestration:** A cyclical, self-correcting state machine built with LangGraph.
* **LLM Engine:** Open-source models, with generation bound by strict structural output schemas.
* **CI/CD Pipeline:** A containerized Go-based Dagger pipeline that dynamically pulls data, executes Pytest and evaluate.
* **Observability:** Complete experiment lineage and evaluation metric tracking logged via a persistent MLflow server.

---

## 🗂️ Project Roadmap & Components

### Stage 1: Data Inventory
The foundational layer consists of structurally deep PDF documents forming the regulatory landscape:
* `eu_ai_act_en.pdf` (European Union / English) - Binding Regulation
* `eu_ai_act_sk.pdf` (European Union / Slovak) - Binding Regulation
* `mirri_vizia_ai_2026.pdf` (Slovakia / Slovak) - Strategic Policy / Vision
* `sk_ai_draft_lp_2026_17_vlastny.pdf` (Slovakia / Slovak) - Draft Legislation
* `sk_ai_draft_lp_2026_17_dovodova.pdf` (Slovakia / Slovak) - Explanatory Legislation

### Stage 2: Utilities
* **Scripts:** `EDA.py`, `helpers.py`, and `visualization.py` handle document profiling, token counting, and distribution plotting.

### Stage 3: Cleaning & Embedding
* Structurally aware chunking strategies preserve strict legal clauses. Vector embeddings are generated using `HuggingFaceEmbeddings` and stored locally in a Chroma vector database.

### Stage 4: Multi-Agent Orchestration (LangGraph)
LegGuard utilizes a specialized "persona" workflow:
1. **The Memory Ledger (`state.py`):** Centralized `GraphState` ensuring state mutations are tightly controlled.
2. **The Gatekeeper (`guardrail.py`):** Evaluates raw prompts for injections or off-topic requests, protecting downstream RAG queries.
3. **The Researcher (`researcher.py`):** Handles heavy RAG tasks, enforces strict language overrides and physical citation rules.
4. **The Auditor (`auditor.py`):** Automated peer-reviewer checking drafts against the source context for hallucinations and groundedness.
5. **The Orchestrator (`graph.py`):** Compiles nodes via Conditional Edges, allowing the system to self-correct until the response is legally perfect.

### Stage 5: Evaluation
Evaluation validates agent responses against expected substring metrics, flags and citation requirements. 

### Stage 6: Code Tests
A 100% green `pytest` suite ensuring pipeline resiliency, graph routing integrity, schema validations, and node-specific state mutations.

---
## 🔮 Future Roadmap (v2.0)

The next iteration of **LegGuard** will focus on scaling evaluation sophistication and improving agent dynamics:

* **Live Telemetry:** Seamlessly stream and visualize multi-agent metrics dynamically as the Dagger pipeline runs via MLflow.
* **Agent Optimization:** Relax strict system prompts to enable a more fluid, nuanced peer-review exchange between the Researcher and Auditor agents.
* **LLM-as-a-Judge:** Replace rigid string-matching with dynamic LLM evaluations to effectively catch complex edge cases and hallucinations.
---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.12+
* Docker & [Dagger](https://dagger.io/)
* Cloudflare R2 API Keys
* Together AI API Key


### 2. Run the Main Application
Start the core application directly:
```bash
uv run python src/main.py