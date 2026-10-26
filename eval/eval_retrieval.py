"""Measure retrieval quality of each search method on the retrieval test set.

Metrics (higher is better):
- Recall@1: share of queries whose first result is relevant
- Recall@4: share of queries with a relevant chunk in the top 4 (what the agent sees)
- MRR:      mean of 1/rank of the first relevant result (0 if not in the top 10)

Run from the project root:
    python eval/eval_retrieval.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
sys.path.append(str(EVAL_DIR))
import config  # noqa: E402
from retrieval_questions import RETRIEVAL_QUESTIONS  # noqa: E402
from tools.rag_tool import SEARCH_METHODS, search_docs  # noqa: E402

MAX_RANK = 10


def first_relevant_rank(result_ids: list[str], relevant: list[str]) -> int | None:
    """1-based rank of the first relevant chunk, or None if none was returned."""
    for rank, chunk_id in enumerate(result_ids, start=1):
        if chunk_id in relevant:
            return rank
    return None


def evaluate_method(method: str) -> pd.DataFrame:
    """Rank of the first relevant chunk for every query, for one method."""
    rows = []
    for q in RETRIEVAL_QUESTIONS:
        ids = [c["id"] for c in search_docs(q["query"], k=MAX_RANK, method=method)]
        rows.append({"method": method, "query": q["query"], "rank": first_relevant_rank(ids, q["relevant"])})
    return pd.DataFrame(rows)


def metrics(df: pd.DataFrame) -> dict:
    """Recall@1, Recall@4 and MRR from a table of ranks."""
    rank = df["rank"]
    return {"recall@1": round((rank == 1).mean(), 3),
            "recall@4": round((rank <= 4).mean(), 3),
            "mrr": round((1 / rank).fillna(0).mean(), 3)}


def main() -> None:
    """Evaluate all methods, print a summary and the misses, save the results."""
    all_ranks = pd.concat([evaluate_method(m) for m in SEARCH_METHODS])
    summary = {m: metrics(all_ranks[all_ranks["method"] == m]) for m in SEARCH_METHODS}
    print(pd.DataFrame(summary).T.to_string())
    wide = all_ranks.pivot(index="query", columns="method", values="rank")
    print("\nRank of the first relevant chunk per query (NaN = not in top 10):")
    print(wide.to_string())
    out = config.RESULTS_DIR / "retrieval_results.json"
    out.write_text(json.dumps({"summary": summary, "ranks": all_ranks.to_dict("records")}, indent=2),
                   encoding="utf-8")
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
