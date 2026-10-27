"""Fault injection: prove that the agent recovers from a failed SQL query.

The first run_sql call is forced to fail with a realistic Athena syntax error.
Every later call runs normally. The test passes when the agent:
1. received the error (one tool error was counted),
2. tried again (at least two SQL calls),
3. still reached the correct answer.

Run from the project root:
    python eval/fault_injection.py
"""
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.append(str(EVAL_DIR.parent / "src"))
sys.path.append(str(EVAL_DIR))
import config  # noqa: E402
import agent.investigator as investigator  # noqa: E402
from run_eval import EXPECTED_PATH, score_answer  # noqa: E402
from tools.athena_tool import AthenaQueryError  # noqa: E402

QUESTION_ID = "q06"  # top RunInstances IP and its count: needs at least one SQL query
FAKE_ERROR = "line 1:42: mismatched input 'FORM'. Expecting: <EOF>"


def make_failing_once(real_run_sql):
    """Wrap run_sql so that only its first call raises a syntax error."""
    calls = {"n": 0}

    def run_sql(sql: str, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise AthenaQueryError(FAKE_ERROR)
        return real_run_sql(sql, *args, **kwargs)

    return run_sql


def main() -> None:
    """Run one question with the injected fault and report the three checks."""
    config.CLAUDE_MODEL = "claude-haiku-5-5"
    item = next(i for i in json.loads(EXPECTED_PATH.read_text(encoding="utf-8")) if i["id"] == QUESTION_ID)
    investigator.run_sql = make_failing_once(investigator.run_sql)  # the agent looks it up here

    run = investigator.run_agent(item["question"])
    checks = {
        "received the error": run["tool_errors"] == 1,
        "tried again": run["tool_calls"].count("run_sql") >= 2,
        "correct answer": all(score_answer(run["answer"], item["facts"])),
    }
    print(f"\n\nANSWER:\n{run['answer'][:400]}\n")
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print("\nSelf-correction works." if all(checks.values()) else "\nSelf-correction FAILED.")


if __name__ == "__main__":
    main()
