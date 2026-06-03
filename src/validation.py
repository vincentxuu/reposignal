"""Validation boundaries for RepoSignal datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from src.quality import EXPECTED_COLUMNS, summarize_quality


@dataclass
class DataValidationError(ValueError):
    """Raised when a pipeline asset violates its dataframe contract."""

    issues: list[str]

    def __str__(self) -> str:
        return "; ".join(self.issues)


def validate_cicd_dataframe(df: pl.DataFrame) -> dict[str, Any]:
    """Validate the processed CI/CD dataframe at pipeline asset boundaries."""
    quality = summarize_quality(df)
    issues = []
    if quality["missing_columns"]:
        issues.append(f"Missing required columns: {', '.join(quality['missing_columns'])}")
    if quality["duplicate_count"]:
        issues.append(f"Duplicate workflow rows: {quality['duplicate_count']}")
    if len(df) > 0:
        for column in sorted(EXPECTED_COLUMNS & set(df.columns)):
            if column in {"workflow_path"}:
                continue
            if df[column].null_count() == len(df):
                issues.append(f"Column is entirely null: {column}")
    if issues:
        raise DataValidationError(issues)
    return quality
