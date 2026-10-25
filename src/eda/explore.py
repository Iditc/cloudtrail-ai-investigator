"""Explore the CloudTrail events with pandas.

Each question has a pandas function, and its docstring shows the equivalent
SQL that the agent would send to Athena, so you can learn to read both.

Run from the project root (after src/data/build_parquet.py):
    python src/eda/explore.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def load_events() -> pd.DataFrame:
    """Load the flat events table from Parquet."""
    return pd.read_parquet(config.EVENTS_PARQUET)


def print_header(title: str) -> None:
    """Print a visible section title."""
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def overview(df: pd.DataFrame) -> None:
    """Print the table shape, columns and memory use (like df.info())."""
    print_header("Overview")
    print(f"Rows: {len(df):,}  |  Columns: {df.shape[1]}")
    print(f"Memory: {df.memory_usage(deep=True).sum() / 1e6:.0f} MB\n")
    print(df.dtypes.to_string())


def q1_date_range(df: pd.DataFrame) -> None:
    """Q1: what is the date range of the logs?

    SQL equivalent:
        SELECT MIN(eventTime) AS first_event, MAX(eventTime) AS last_event
        FROM cloudtrail_logs;
    """
    print_header("Q1: Date range")
    first, last = df["eventTime"].min(), df["eventTime"].max()
    print(f"First: {first}\nLast:  {last}\nSpan:  {last - first}")


def q2_run_instances_outcome(df: pd.DataFrame) -> None:
    """Q2: how many RunInstances calls succeeded vs. failed, by error code?

    SQL equivalent:
        SELECT errorCode, COUNT(*) AS n
        FROM cloudtrail_logs
        WHERE eventName = 'RunInstances'
        GROUP BY errorCode
        ORDER BY n DESC;
    """
    print_header("Q2: RunInstances outcome (NaN = success)")
    run = df[df["eventName"] == "RunInstances"]
    # Drop category values that never appear in this subset (otherwise listed with 0)
    counts = run["errorCode"].cat.remove_unused_categories().value_counts(dropna=False)
    share = (counts / len(run) * 100).round(1)
    print(pd.DataFrame({"n": counts, "percent": share}).to_string())


def q3_top_ips_run_instances(df: pd.DataFrame) -> None:
    """Q3 (your exercise): which 5 IPs made the most RunInstances calls?

    SQL equivalent:
        SELECT sourceIPAddress, COUNT(*) AS n
        FROM cloudtrail_logs
        WHERE eventName = 'RunInstances'
        GROUP BY sourceIPAddress
        ORDER BY n DESC
        LIMIT 5;

    Hint: same pattern as q2, on a different column, plus .head(5).
    """
    print_header("Q3: Top 5 IPs for RunInstances")
    # TODO: write your pandas code here and print the result
    print("Not implemented yet")


def q4_run_instances_per_day(df: pd.DataFrame) -> None:
    """Q4 (your exercise): when did the RunInstances wave start?

    SQL equivalent:
        SELECT substr(eventTime, 1, 10) AS day, COUNT(*) AS n
        FROM cloudtrail_logs
        WHERE eventName = 'RunInstances'
        GROUP BY substr(eventTime, 1, 10)
        ORDER BY day;

    Hint: filter RunInstances, then count rows per day, e.g. with
    .set_index("eventTime").resample("D").size(). Print the 10 busiest
    days, then pass the daily series to save_daily_plot().
    """
    print_header("Q4: RunInstances per day")
    # TODO: build a Series indexed by day with the number of calls per day
    daily = None
    if daily is None:
        print("Not implemented yet")
        return
    save_daily_plot(daily, "RunInstances calls per day", "run_instances_per_day.png")


def save_daily_plot(daily: pd.Series, title: str, file_name: str) -> None:
    """Save a line plot of a daily count series to results/figures."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 4))
    daily.plot(ax=ax)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Calls per day")
    fig.tight_layout()
    path = config.FIGURES_DIR / file_name
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"Plot saved: {path}")


def main() -> None:
    """Run all exploration questions in order."""
    df = load_events()
    overview(df)
    q1_date_range(df)
    q2_run_instances_outcome(df)
    q3_top_ips_run_instances(df)
    q4_run_instances_per_day(df)


if __name__ == "__main__":
    main()
