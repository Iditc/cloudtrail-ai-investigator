"""Run the agent on the evaluation questions and score its answers.

Scoring: a question passes when every expected fact appears in the answer
(any acceptable spelling). Numbers must match as whole numbers, so '2' does not
match inside '2019'. Also records steps, tool calls, tokens, cost and time.

Run from the project root:
    python eval/run_eval.py                                # all questions, default model
    python eval/run_eval.py q01 q06                        # only some questions
    python eval/run_eval.py --model claude-haiku-5-5       # another model
"""
import argparse
import contextlib
import io
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
import config  # noqa: E402
from agent.investigator import run_agent  # noqa: E402

EXPECTED_PATH = EVAL_DIR / "expected.json"

# USD per 1M tokens (input, output), Claude API list prices
PRICES = {"claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50),
          "claude-opus-5-5": (4.00, 20.00)}


def normalize(answer: str) -> str:
    """Lowercase, drop markdown symbols and thousands separators (1,299,186 -> 1299186)."""
    answer = answer.lower().replace("`", "").replace("*", "")
    return re.sub(r"(?<=\d),(?=\d{3})", "", answer)


def variant_found(variant: str, answer: str) -> bool:
    """Check one spelling: whole-number match for numbers, substring otherwise."""
    variant = variant.lower()
    if variant.isdigit():
        return re.search(rf"(?<![\d.]){variant}(?![\d])", answer) is not None
    return variant in answer


def score_answer(answer: str, facts: list[list[str]]) -> list[bool]:
    """For each expected fact, did any acceptable spelling appear in the answer?"""
    norm = normalize(answer)
    return [any(variant_found(v, norm) for v in fact) for fact in facts]


def run_question(item: dict) -> dict:
    """Run the agent on one question (hiding its progress output) and score it."""
    start = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        run = run_agent(item["question"])
    found = score_answer(run["answer"], item["facts"])
    price_in, price_out = PRICES[config.CLAUDE_MODEL]
    cost = (run["input_tokens"] * price_in + run["output_tokens"] * price_out) / 1e6
    return {**item, **run, "found": found, "passed": all(found),
            "seconds": round(time.time() - start, 1), "cost_usd": round(cost, 5)}


def summarize(results: list[dict]) -> dict:
    """Overall metrics across all evaluated questions."""
    n = len(results)
    facts = [f for r in results for f in r["found"]]
    label = f"{config.CLAUDE_MODEL}+defense" if config.INJECTION_DEFENSE else config.CLAUDE_MODEL
    return {"model": label, "questions": n,
            "accuracy": round(sum(r["passed"] for r in results) / n, 3),
            "fact_recall": round(sum(facts) / len(facts), 3),
            "total_cost_usd": round(sum(r["cost_usd"] for r in results), 3),
            "avg_seconds": round(sum(r["seconds"] for r in results) / n, 1),
            "avg_steps": round(sum(r["steps"] for r in results) / n, 1)}


def parse_args() -> argparse.Namespace:
    """Command line: optional question ids and an optional model name."""
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", help="question ids to run (default: all)")
    parser.add_argument("--model", default=config.CLAUDE_MODEL, choices=sorted(PRICES))
    parser.add_argument("--defense", action="store_true", help="turn on the prompt-injection defenses")
    return parser.parse_args()


def main() -> None:
    """Run the selected questions, print a table and save all results."""
    args = parse_args()
    config.CLAUDE_MODEL = args.model  # the agent reads the model from config at call time
    config.INJECTION_DEFENSE = args.defense
    items = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    if args.ids:
        items = [i for i in items if i["id"] in args.ids]
    label = f"{args.model}+defense" if args.defense else args.model
    results_path = config.RESULTS_DIR / f"eval_{label}.json"
    results = []
    for item in items:
        r = run_question(item)
        results.append(r)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"{r['id']}  {mark}  facts {sum(r['found'])}/{len(r['found'])}  "
              f"steps {r['steps']}  {r['seconds']:>5}s  ${r["cost_usd"]:.4f}  {r['question'][:55]}")
    summary = summarize(results)
    print(f"\n{json.dumps(summary, indent=2)}")
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps({"run_at": datetime.now().isoformat(timespec="seconds"),
                                        "summary": summary, "results": results}, indent=2),
                            encoding="utf-8")
    print(f"Saved to {results_path}")


if __name__ == "__main__":
    main()
