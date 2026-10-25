"""Quick look at the raw CloudTrail data before querying it with Athena.

Run from the project root:
    python src/setup_aws/peek_logs.py
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

KEY_FIELDS = ["eventTime", "eventName", "eventSource", "sourceIPAddress",
              "userAgent", "errorCode", "userIdentity"]


def load_records(path: Path) -> list[dict]:
    """Load the list of CloudTrail records from one gzipped JSON file."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)["Records"]


def show_record(record: dict) -> None:
    """Print only the most important fields of one record."""
    sample = {k: record.get(k) for k in KEY_FIELDS}
    print(json.dumps(sample, indent=2))


def show_top(records: list[dict], field: str, n: int = 10) -> None:
    """Print the n most common values of a top-level field."""
    print(f"\nTop {n} values of '{field}':")
    for value, count in Counter(r.get(field) for r in records).most_common(n):
        print(f"  {count:>7,}  {value}")


def main() -> None:
    """Show one record and simple counts from the first log file."""
    first_file = sorted(config.LOGS_EXTRACTED_DIR.rglob("*.json.gz"))[0]
    records = load_records(first_file)
    print(f"File: {first_file.name}  |  records: {len(records):,}\n")
    print("One record (key fields only):")
    show_record(records[0])
    show_top(records, "eventName")
    show_top(records, "errorCode", n=5)


if __name__ == "__main__":
    main()
