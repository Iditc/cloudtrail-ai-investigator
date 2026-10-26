"""Compare evaluation results across models (reads results/eval_<model>.json).

Run from the project root, after run_eval.py for each model:
    python eval/compare_models.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
import config  # noqa: E402


def load_results() -> pd.DataFrame:
    """One row per (model, question) from every results file."""
    rows = []
    for path in sorted(config.RESULTS_DIR.glob("eval_claude-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data["results"]:
            rows.append({"model": data["summary"]["model"], "id": r["id"], "topic": r["topic"],
                         "passed": r["passed"], "steps": r["steps"], "seconds": r["seconds"],
                         "cost_usd": r["cost_usd"]})
    return pd.DataFrame(rows)


def overall_table(df: pd.DataFrame) -> pd.DataFrame:
    """Accuracy, total cost, average time and steps per model."""
    return df.groupby("model").agg(
        questions=("id", "count"), accuracy=("passed", "mean"),
        total_cost_usd=("cost_usd", "sum"), avg_seconds=("seconds", "mean"),
        avg_steps=("steps", "mean")).round(3)


def topic_table(df: pd.DataFrame) -> pd.DataFrame:
    """Accuracy per question topic (rows) and model (columns)."""
    return df.pivot_table(index="topic", columns="model", values="passed", aggfunc="mean").round(2)


def disagreements(df: pd.DataFrame) -> pd.DataFrame:
    """Questions where the models did not all get the same pass/fail result."""
    wide = df.pivot_table(index="id", columns="model", values="passed", aggfunc="first")
    return wide[wide.nunique(axis=1) > 1]


def main() -> None:
    """Print the comparison tables."""
    df = load_results()
    if df.empty:
        sys.exit("No results found. Run eval/run_eval.py --model <name> first.")
    print("Overall\n", overall_table(df).to_string(), sep="")
    print("\nAccuracy by topic\n", topic_table(df).to_string(), sep="")
    diff = disagreements(df)
    print("\nQuestions where models disagree\n", diff.to_string() if len(diff) else "(none)", sep="")


if __name__ == "__main__":
    main()
