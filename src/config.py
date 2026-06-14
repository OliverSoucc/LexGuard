import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
TEST_DATA_DIR = DATA_DIR / "test"
BASELINE_EVAL_SET_PATH = TEST_DATA_DIR / "baseline_eval_set.json"
QUICK_EVAL_SET_PATH = TEST_DATA_DIR / "quick_eval_set.json"
EMBEDDING_METRICS_PATH = DATA_DIR / "embedding_metrics.json"
MLFLOW_DB_PATH = PROJECT_ROOT / "mlflow.db"


# Retrieval / embeddings
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 200
RETRIEVAL_TOP_K = 4

# LLM models
RESEARCHER_MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
AUDITOR_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-Turbo"
GUARDRAIL_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-Turbo"

# Experiments
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB_PATH}")
EXPERIMENT_DATA_PIPELINE = "LexGuard_Data_Pipeline"
EXPERIMENT_EVALUATION = "LexGuard_v1_Evaluation"
EXPERIMENT_CHAT = "LexGuard_Agent_General_Chat"

# Evaluation / agent settings
MAX_AUDITOR_RETRIES = 3
EVAL_PASS_THRESHOLD = 0.72

# Optional behavior flags
DRAW_GRAPH_ENV_VAR = "LEXGUARD_DRAW_GRAPH"