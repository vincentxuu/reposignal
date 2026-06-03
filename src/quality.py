"""Data quality checks for pipeline outputs."""

from __future__ import annotations

from typing import Any

import polars as pl


EXPECTED_COLUMNS = {
    "repo",
    "workflow_name",
    "workflow_path",
    "crawl_date",
    "triggers",
    "job_names",
    "uses_matrix",
    "actions_normalized",
    "has_permissions_block",
    "has_security_scan",
}


def summarize_quality(df: pl.DataFrame) -> dict[str, Any]:
    """Compute row-level quality metrics used by reports and run metadata."""
    columns = set(df.columns)
    missing_columns = sorted(EXPECTED_COLUMNS - columns)
    duplicate_count = 0
    if {"repo", "workflow_name", "workflow_path"}.issubset(columns) and len(df) > 0:
        duplicate_count = len(df) - len(df.unique(subset=["repo", "workflow_name", "workflow_path"]))

    null_rates = {}
    for column in sorted(columns):
        null_rates[column] = round(df[column].null_count() / len(df) * 100, 2) if len(df) else 0.0

    repo_count = df["repo"].n_unique() if "repo" in columns and len(df) else 0
    workflow_count = len(df)
    status = "pass"
    issues = []
    if missing_columns:
        status = "fail"
        issues.append(f"Missing columns: {', '.join(missing_columns)}")
    if duplicate_count:
        status = "warn" if status == "pass" else status
        issues.append(f"Duplicate workflow rows: {duplicate_count}")

    return {
        "status": status,
        "row_count": workflow_count,
        "repo_count": repo_count,
        "missing_columns": missing_columns,
        "duplicate_count": duplicate_count,
        "null_rates": null_rates,
        "issues": issues,
    }
