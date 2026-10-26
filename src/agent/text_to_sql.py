"""Day 2: ask a question in English, let Claude write the SQL, run it on Athena.

No agent loop yet: one LLM call, one query. If the SQL fails, the error is
printed (day 3 adds self-correction).

Run from the project root:
    python src/agent/text_to_sql.py "Which 5 IPs made the most RunInstances calls?"
"""
import sys
from pathlib import Path

import anthropic

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402  (also loads ANTHROPIC_API_KEY from .env)
from agent.prompts import SQL_SYSTEM_PROMPT  # noqa: E402
from tools.athena_tool import AthenaQueryError, run_sql  # noqa: E402


def clean_sql(text: str) -> str:
    """Strip markdown fences and whitespace in case the model adds them."""
    lines = [line for line in text.strip().splitlines() if not line.strip().startswith("```")]
    return "\n".join(lines).strip().rstrip(";")


def question_to_sql(client: anthropic.Anthropic, question: str) -> str:
    """Ask Claude to translate one question into one SQL query."""
    response = client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        output_config={"effort": "low"},  # simple task: keep it fast and cheap
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the model declines, the API retries on another model
        system=SQL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"The model declined this question: {response.stop_details}")
    text = "".join(block.text for block in response.content if block.type == "text")
    usage = response.usage
    print(f"[tokens: {usage.input_tokens} in, {usage.output_tokens} out]")
    return clean_sql(text)


def main() -> None:
    """Read the question from the command line, then print the SQL and its result."""
    if len(sys.argv) < 2:
        sys.exit('Usage: python src/agent/text_to_sql.py "your question"')
    question = sys.argv[1]
    client = anthropic.Anthropic()

    sql = question_to_sql(client, question)
    print(f"\nSQL:\n{sql}\n")
    try:
        result = run_sql(sql)
    except AthenaQueryError as error:
        sys.exit(f"Athena error: {error}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
