"""Record one real agent run and save it as an SVG image for the README.

The image shows the question, every tool call the agent made, and its final answer.

Run from the project root:
    python src/make_demo.py
    python src/make_demo.py "your question" --model claude-sonnet-5-5
"""
import argparse
import contextlib
import io
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel

sys.path.append(str(Path(__file__).resolve().parent))
import config  # noqa: E402
from agent.investigator import run_agent  # noqa: E402

DEFAULT_QUESTION = "Did anyone try to stop CloudTrail logging, and did it work?"
OUT_PATH = config.PROJECT_ROOT / "assets" / "demo.svg"


def style_trace_line(line: str) -> str:
    """Color the agent's progress lines: steps, SQL, searches, errors."""
    stripped = escape(line.strip())  # '[step 1]' would otherwise be read as rich markup
    if stripped.startswith("\\[step"):
        return f"[bold cyan]{stripped}[/]"
    if stripped.startswith("SQL:"):
        return f"  [yellow]SQL[/] {stripped[4:].strip()}"
    if stripped.startswith("SEARCH:"):
        return f"  [magenta]SEARCH[/] {stripped[7:].strip()}"
    if "ERROR" in stripped:
        return f"  [red]{stripped}[/]"
    return f"  [dim]{stripped}[/]"


def main() -> None:
    """Run the agent once, render question, trace and answer, and save as SVG."""
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--model", default="claude-haiku-5-5")
    args = parser.parse_args()
    config.CLAUDE_MODEL = args.model

    trace = io.StringIO()
    with contextlib.redirect_stdout(trace):
        run = run_agent(args.question)

    console = Console(record=True, width=110)
    console.print(Panel(args.question, title="Analyst question", border_style="cyan"))
    for line in trace.getvalue().splitlines():
        if line.strip():
            console.print(style_trace_line(line), soft_wrap=False, overflow="ellipsis", no_wrap=True)
    console.print(Panel(Markdown(run["answer"]), title=f"Answer ({args.model})", border_style="green"))
    OUT_PATH.parent.mkdir(exist_ok=True)
    console.save_svg(str(OUT_PATH), title="CloudTrail AI Investigator")
    print(f"Saved {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
