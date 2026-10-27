"""Central project configuration: file paths and AWS settings.

Values come from the .env file in the project root (see .env.example).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Local paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LOGS_ARCHIVE = RAW_DIR / "flaws_cloudtrail_logs.tar"
LOGS_EXTRACTED_DIR = RAW_DIR / "extracted"
PROCESSED_DIR = DATA_DIR / "processed"
EVENTS_PARQUET = PROCESSED_DIR / "cloudtrail_events.parquet"
DOCS_DIR = DATA_DIR / "docs"

# RAG knowledge base
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"  # hand-written docs, committed to git
MITRE_JSON = RAW_DIR / "mitre" / "enterprise-attack.json"  # from github.com/mitre/cti
CHROMA_DIR = PROJECT_ROOT / "chroma_db"  # local vector DB, not committed
CHROMA_COLLECTION = "security_knowledge"
RAG_METHOD = "hybrid"  # "vector", "bm25" or "hybrid"; hybrid had the best Recall@4 (eval/eval_retrieval.py)
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# AWS settings
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "cloudtrail-detective")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_LOGS_PREFIX = "cloudtrail/"
S3_ATHENA_RESULTS = f"s3://{S3_BUCKET}/athena-results/"

ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "cloudtrail_detective")
ATHENA_TABLE = os.getenv("ATHENA_TABLE", "cloudtrail_logs")
ATHENA_MAX_ROWS = 100  # rows returned to the LLM, to keep prompts small

# Day 9: prompt-injection test table (a view = real logs + a few poisoned events)
ATHENA_INJECTION_VIEW = "cloudtrail_logs_injected"
S3_INJECTION_PREFIX = "injection/"
# Defense prompt rules + tool results wrapped as untrusted data. On by default since day 9:
# it cut subtle-attack success from 29% to 0% with no loss of accuracy (eval/injection_test.py)
INJECTION_DEFENSE = True

# LLM settings (ANTHROPIC_API_KEY is read from .env by the SDK)
CLAUDE_MODEL = "claude-sonnet-5-5"
