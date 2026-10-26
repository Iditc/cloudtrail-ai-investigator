"""Compute the expected answers from the data and save them to eval/expected.json.

Run once from the project root (after src/data/build_parquet.py):
    python eval/build_expected.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
sys.path.append(str(EVAL_DIR))
import config  # noqa: E402
from questions import QUESTIONS  # noqa: E402

EXPECTED_PATH = EVAL_DIR / "expected.json"


def build_expected(df: pd.DataFrame) -> list[dict]:
    """Run each question's pandas function and collect the expected facts."""
    return [{"id": q["id"], "topic": q["topic"], "question": q["question"], "facts": q["facts"](df)}
            for q in QUESTIONS]


def main() -> None:
    """Load the events, compute expected facts and save them as JSON."""
    df = pd.read_parquet(config.EVENTS_PARQUET)
    expected = build_expected(df)
    EXPECTED_PATH.write_text(json.dumps(expected, indent=2), encoding="utf-8")
    for item in expected:
        print(f"{item['id']}  {[fact[0] for fact in item['facts']]}")
    print(f"\nSaved {len(expected)} questions to {EXPECTED_PATH.name}")


if __name__ == "__main__":
    main()
