"""Small MCP client to test the server without Claude Desktop.

It starts server.py the same way a host would (over stdio), lists the tools,
and calls search_docs and run_sql once each.

Run from the project root:
    python src/mcp_server/try_client.py
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client

SERVER = Path(__file__).resolve().parent / "server.py"


async def main() -> None:
    """Connect to the server, list its tools and call two of them."""
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [tool.name for tool in tools.tools])

            result = await session.call_tool("search_docs", {"query": "who is the root user"})
            print("\nsearch_docs ->", result.content[0].text[:300], "...")

            sql = ("SELECT eventname, COUNT(*) AS n FROM cloudtrail_detective.cloudtrail_logs "
                   "GROUP BY eventname ORDER BY n DESC LIMIT 3")
            result = await session.call_tool("run_sql", {"sql": sql})
            print("\nrun_sql ->", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
