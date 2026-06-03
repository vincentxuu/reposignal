"""Tests for validation boundaries and Dagster definitions."""

import polars as pl
import pytest

from src.dagster_defs import defs
from src.validation import DataValidationError, validate_cicd_dataframe


def test_validate_cicd_dataframe_accepts_contract_shape() -> None:
    df = pl.DataFrame(
        {
            "repo": ["a/b"],
            "workflow_name": ["ci"],
            "workflow_path": [".github/workflows/ci.yml"],
            "crawl_date": ["2026-03-29"],
            "triggers": [["push"]],
            "job_names": [["test"]],
            "uses_matrix": [False],
            "actions_normalized": [["actions/checkout"]],
            "has_permissions_block": [True],
            "has_security_scan": [False],
        }
    )

    quality = validate_cicd_dataframe(df)

    assert quality["status"] == "pass"
    assert quality["row_count"] == 1


def test_validate_cicd_dataframe_rejects_duplicates() -> None:
    df = pl.DataFrame(
        {
            "repo": ["a/b", "a/b"],
            "workflow_name": ["ci", "ci"],
            "workflow_path": [".github/workflows/ci.yml", ".github/workflows/ci.yml"],
            "crawl_date": ["2026-03-29", "2026-03-29"],
            "triggers": [["push"], ["push"]],
            "job_names": [["test"], ["test"]],
            "uses_matrix": [False, False],
            "actions_normalized": [["actions/checkout"], ["actions/checkout"]],
            "has_permissions_block": [True, True],
            "has_security_scan": [False, False],
        }
    )

    with pytest.raises(DataValidationError, match="Duplicate workflow rows"):
        validate_cicd_dataframe(df)


def test_dagster_definitions_expose_pipeline_assets() -> None:
    asset_names = {
        next(iter(asset.keys)).path[-1]
        for asset in defs.assets or []
    }

    assert {
        "raw_workflows",
        "extended_batch1",
        "extended_batch2",
        "extended_batch3",
        "cicd_parquet",
        "analysis_json",
        "report_markdown",
    } <= asset_names
