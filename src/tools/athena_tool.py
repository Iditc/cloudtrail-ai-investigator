"""Tool: run a SQL query on Athena and return the result as a DataFrame.

This module knows nothing about LLMs or agents. It only runs SQL.
"""
import sys
import time
from pathlib import Path

import boto3
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


class AthenaQueryError(Exception):
    """Raised when Athena rejects or fails a query (the message says why)."""


def get_athena_client():
    """Create an Athena client with the project's AWS profile and Region."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    return session.client("athena")


def check_read_only(sql: str) -> None:
    """Allow only SELECT / WITH queries, so the LLM can never change data."""
    first_word = sql.strip().split(None, 1)[0].upper() if sql.strip() else ""
    if first_word not in ("SELECT", "WITH"):
        raise AthenaQueryError(f"Only SELECT queries are allowed, got: {first_word or 'empty query'}")


def wait_for_query(athena, query_id: str) -> dict:
    """Poll Athena until the query finishes; return its final status."""
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_id)["QueryExecution"]["Status"]
        if status["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return status
        time.sleep(1)


def fetch_rows(athena, query_id: str, max_rows: int) -> pd.DataFrame:
    """Read up to max_rows result rows into a DataFrame (first row is the header)."""
    paginator = athena.get_paginator("get_query_results")
    rows = []
    for page in paginator.paginate(QueryExecutionId=query_id):
        for row in page["ResultSet"]["Rows"]:
            rows.append([cell.get("VarCharValue") for cell in row["Data"]])
        if len(rows) > max_rows:
            break
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows[1:max_rows + 1], columns=rows[0])


def run_sql(sql: str, max_rows: int = config.ATHENA_MAX_ROWS) -> pd.DataFrame:
    """Run a read-only SQL query on Athena and return the result rows.

    Raises AthenaQueryError with Athena's own error message if the query fails.
    """
    check_read_only(sql)
    athena = get_athena_client()
    query_id = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": config.ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": config.S3_ATHENA_RESULTS},
    )["QueryExecutionId"]
    status = wait_for_query(athena, query_id)
    if status["State"] != "SUCCEEDED":
        raise AthenaQueryError(status.get("StateChangeReason", status["State"]))
    return fetch_rows(athena, query_id, max_rows)
