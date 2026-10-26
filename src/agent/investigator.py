"""The agent loop (day 3) with RAG (day 4).

Claude gets two tools: run_sql (facts from Athena) and search_docs (meaning,
from the vector knowledge base). It decides when to call each one, sees the
result (or the error), can fix and retry, and finally answers in plain English.
The loop is written by hand on purpose, to show what an "agent" really is.

Run from the project root:
    python src/agent/investigator.py "Did anyone try to stop CloudTrail logging?"
"""
import sys
from pathlib import Path

import anthropic

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402  (also loads ANTHROPIC_API_KEY from .env)
from agent.prompts import AGENT_SYSTEM_PROMPT  # noqa: E402
from tools.athena_tool import AthenaQueryError, run_sql  # noqa: E402
from tools.rag_tool import format_for_llm, search_docs  # noqa: E402

MAX_STEPS = 8  # safety limit: stop the loop even if Claude keeps calling tools

RUN_SQL_TOOL = {
    "name": "run_sql",
    "description": (
        "Run one read-only SQL query on the CloudTrail table in Amazon Athena. "
        "Returns the result rows as CSV, or the Athena error message if the query fails."
    ),
    "strict": True,  # the API guarantees the input matches the schema
    "input_schema": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "One Athena SQL SELECT query."}},
        "required": ["sql"],
        "additionalProperties": False,
    },
}

SEARCH_DOCS_TOOL = {
    "name": "search_docs",
    "description": (
        "Semantic search in a knowledge base: context about this dataset and its identities, "
        "what CloudTrail actions and error codes mean, and MITRE ATT&CK cloud techniques. "
        "Returns the 4 closest text chunks with their source."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to look up, in plain English."}},
        "required": ["query"],
        "additionalProperties": False,
    },
}


def execute_run_sql(tool_input: dict) -> tuple[str, bool]:
    """Run the SQL from a tool call. Return (text for Claude, is_error)."""
    sql = tool_input["sql"]
    print(f"\n  SQL: {' '.join(sql.split())}")
    try:
        result = run_sql(sql)
    except AthenaQueryError as error:
        print(f"  -> ERROR: {error}")
        return f"Query failed: {error}", True
    print(f"  -> {len(result)} rows")
    return f"{len(result)} rows:\n{result.to_csv(index=False)}", False


def execute_search_docs(tool_input: dict) -> tuple[str, bool]:
    """Search the knowledge base. Return (text for Claude, is_error)."""
    query = tool_input["query"]
    print(f"\n  SEARCH: {query}")
    chunks = search_docs(query)
    for rank, chunk in enumerate(chunks, start=1):
        print(f"  -> {rank}. {chunk['title']}")
    return format_for_llm(chunks), False


TOOL_FUNCTIONS = {"run_sql": execute_run_sql, "search_docs": execute_search_docs}


# Models that accept the server-side refusal fallback (Haiku does not)
FALLBACK_MODELS = {"claude-sonnet-5-5", "claude-opus-5-5"}


def call_claude(client: anthropic.Anthropic, messages: list):
    """Send the conversation so far to Claude, with both tools available."""
    extra = {}
    if config.CLAUDE_MODEL in FALLBACK_MODELS:
        extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    return client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},  # multi-step tool use: medium is a good start
        system=AGENT_SYSTEM_PROMPT,
        tools=[RUN_SQL_TOOL, SEARCH_DOCS_TOOL],
        messages=messages,
        **extra,
    )


def run_tool_calls(response) -> list:
    """Execute every tool call in Claude's response and build the tool results."""
    results = []
    for block in response.content:
        if block.type == "tool_use":
            text, is_error = TOOL_FUNCTIONS[block.name](block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": text, "is_error": is_error})
    return results


def run_agent(question: str) -> dict:
    """Run the agent loop for one question.

    Returns the final answer plus run statistics (steps, tool calls, tokens),
    which the evaluation uses to measure cost and behaviour.
    """
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": question}]
    stats = {"steps": 0, "tool_calls": [], "tool_errors": 0, "input_tokens": 0, "output_tokens": 0}
    for step in range(1, MAX_STEPS + 1):
        print(f"\n[step {step}]", end="")
        response = call_claude(client, messages)
        stats["steps"] = step
        stats["input_tokens"] += response.usage.input_tokens
        stats["output_tokens"] += response.usage.output_tokens
        # Keep Claude's full turn (including tool calls) in the history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            return {"answer": f"The model declined: {response.stop_details}", **stats}
        if response.stop_reason != "tool_use":
            answer = "".join(b.text for b in response.content if b.type == "text")
            return {"answer": answer, **stats}
        stats["tool_calls"] += [b.name for b in response.content if b.type == "tool_use"]
        tool_results = run_tool_calls(response)
        # Failed tool calls (e.g. invalid SQL) that Claude must recover from
        stats["tool_errors"] += sum(r["is_error"] for r in tool_results)
        messages.append({"role": "user", "content": tool_results})
    return {"answer": f"Stopped after {MAX_STEPS} steps without a final answer.", **stats}


def ask_agent(question: str) -> str:
    """Run the agent loop for one question and return only Claude's final answer."""
    return run_agent(question)["answer"]


def main() -> None:
    """Read the question from the command line and print the agent's answer."""
    if len(sys.argv) < 2:
        sys.exit('Usage: python src/agent/investigator.py "your question"')
    answer = ask_agent(sys.argv[1])
    print(f"\n\n{'=' * 60}\nANSWER:\n{answer}")


if __name__ == "__main__":
    main()
