"""Consistency check: run every question several times and see if results change.

An agent is not deterministic: the same question can lead to different queries,
searches and answers. One passing run is not proof; a stable pass rate is.

Run from the project root (default: 3 repeats on Haiku 5.5):
    python eval/consistency.py
    python eval/consistency.py --repeats 5 --model claude-sonnet-5-5
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
sys.path.append(str(EVAL_DIR))
import config  # noqa: E402
from run_eval import EXPECTED_PATH, PRICES, run_question  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Command line: number of repeats and model."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--model", default="claude-haiku-5-5", choices=sorted(PRICES))
    return parser.parse_args()


def run_all(items: list[dict], repeats: int) -> pd.DataFrame:
    """Run each question `repeats` times; one row per run."""
    rows = []
    for repeat in range(1, repeats + 1):
        for item in items:
            try:
                r = run_question(item)
            except Exception as error:  # a crash is a failure, but must not stop the whole check
                print(f"repeat {repeat}  {item['id']}  CRASH  {type(error).__name__}: {error}")
                rows.append({"repeat": repeat, "id": item["id"], "topic": item["topic"], "passed": False,
                             "steps": 0, "tool_errors": 0, "sql_calls": 0, "searches": 0,
                             "cost_usd": 0.0, "answer": f"CRASH: {error}"})
                continue
            rows.append({"repeat": repeat, "id": r["id"], "topic": r["topic"], "passed": r["passed"],
                         "steps": r["steps"], "tool_errors": r["tool_errors"],
                         "sql_calls": r["tool_calls"].count("run_sql"),
                         "searches": r["tool_calls"].count("search_docs"),
                         "cost_usd": r["cost_usd"], "answer": r["answer"]})
            print(f"repeat {repeat}  {r['id']}  {'PASS' if r['passed'] else 'FAIL'}  "
                  f"steps {r['steps']}  tool errors {r['tool_errors']}")
    return pd.DataFrame(rows)


def per_question(df: pd.DataFrame) -> pd.DataFrame:
    """Pass rate and behaviour spread per question."""
    return df.groupby("id").agg(
        pass_rate=("passed", "mean"), steps_min=("steps", "min"), steps_max=("steps", "max"),
        tool_errors=("tool_errors", "sum"), searches_min=("searches", "min"),
        searches_max=("searches", "max")).round(2)


def main() -> None:
    """Run the consistency check, print a summary and save all runs."""
    args = parse_args()
    config.CLAUDE_MODEL = args.model
    items = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    df = run_all(items, args.repeats)
    table = per_question(df)
    unstable = table[(table["pass_rate"] < 1) | (table["steps_min"] != table["steps_max"])]
    print(f"\nModel {args.model}, {args.repeats} repeats, {len(df)} runs, cost ${df['cost_usd'].sum():.3f}")
    print(f"Overall pass rate: {df['passed'].mean():.3f}")
    print(f"Questions passed in every run: {(table['pass_rate'] == 1).sum()}/{len(table)}")
    print(f"Runs with at least one tool error: {(df['tool_errors'] > 0).sum()} "
          f"(of which passed: {df[df['tool_errors'] > 0]['passed'].sum()})")
    print("\nQuestions with any variation (pass rate or number of steps):")
    print(unstable.to_string() if len(unstable) else "(none)")
    out = config.RESULTS_DIR / f"consistency_{args.model}.json"
    out.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
