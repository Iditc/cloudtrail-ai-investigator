"""Day 5: MCP server that exposes the investigation tools to any MCP host.

A host such as Claude Desktop starts this script and talks to it over stdio
(standard input/output). The host's own model then decides when to call:
- run_sql:     facts from the CloudTrail logs in Athena
- search_docs: meaning, from the RAG knowledge base
- investigate: the full agent from src/agent/investigator.py

This file is a thin layer: all real work stays in tools/ and agent/.

Run directly (normally the host starts it for you):
    python src/mcp_server/server.py
"""
import contextlib
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

sys.path.append(str(Path(__file__).resolve().parent.parent))
from agent.investigator import ask_agent  # noqa: E402
from tools.athena_tool import AthenaQueryError, run_sql as athena_run_sql  # noqa: E402
from tools.rag_tool import format_for_llm, search_docs as rag_search  # noqa: E402

mcp = MCPServer("cloudtrail-ai-investigator")


@contextlib.contextmanager
def quiet_stdout():
    """Send print() output to stderr: over stdio, stdout is reserved for MCP messages."""
    with contextlib.redirect_stdout(sys.stderr):
        yield


@mcp.tool()
def run_sql(sql: str) -> str:
    """Run one read-only Athena SQL query on the flaws.cloud CloudTrail table
    cloudtrail_detective.cloudtrail_logs. Returns rows as CSV (max 100), or the error."""
    with quiet_stdout():
        try:
            result = athena_run_sql(sql)
        except AthenaQueryError as error:
            return f"Query failed: {error}"
    return f"{len(result)} rows:\n{result.to_csv(index=False)}"


@mcp.tool()
def search_docs(query: str) -> str:
    """Search the knowledge base: dataset context and identities, CloudTrail
    error codes and actions, and MITRE ATT&CK cloud techniques."""
    with quiet_stdout():
        return format_for_llm(rag_search(query))


@mcp.tool()
def investigate(question: str) -> str:
    """Answer a security question about the CloudTrail logs with the full
    investigation agent (it runs its own SQL and searches). Uses the Claude API."""
    with quiet_stdout():
        return ask_agent(question)


if __name__ == "__main__":
    mcp.run(transport="stdio")
