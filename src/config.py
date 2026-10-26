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

# LLM settings (ANTHROPIC_API_KEY is read from .env by the SDK)
CLAUDE_MODEL = "claude-sonnet-5-5"
