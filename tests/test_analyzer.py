"""Tests for the analyzer module."""

import json
from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

from src.analyzer import analyze, _compute_diffs, _empty_results


@pytest.fixture()
def sample_parquet(tmp_path: Path) -> Path:
    """Create a small Parquet file with known test data."""
    df = pl.DataFrame(
        {
            "repo": [
                "org-a/repo-1",
                "org-a/repo-1",
                "org-b/repo-2",
                "org-b/repo-2",
                "org-c/repo-3",
            ],
            "workflow_name": ["ci", "security", "ci", "ai-review", "build"],
            "triggers": [
                ["push", "pull_request"],
                ["push"],
                ["push"],
                ["pull_request"],
                ["push"],
            ],
            "job_names": [["test"], ["scan"], ["test"], ["review"], ["build"]],
            "uses_matrix": [False, False, True, False, False],
            "uses_reusable_workflows": [False, False, False, False, False],
            "actions_used": [
                ["actions/checkout@v4", "actions/setup-python@v5"],
                ["actions/checkout@v4", "aquasecurity/trivy-action@master"],
                ["actions/checkout@v4", "actions/setup-python@v5"],
                ["actions/checkout@v4", "anthropics/claude-code-review@v1"],
                ["actions/checkout@v4", "actions/setup-node@v4"],
            ],
            "actions_normalized": [
                ["actions/checkout", "actions/setup-python"],
                ["actions/checkout", "aquasecurity/trivy-action"],
                ["actions/checkout", "actions/setup-python"],
                ["actions/checkout", "anthropics/claude-code-review"],
                ["actions/checkout", "actions/setup-node"],
            ],
            "has_permissions_block": [True, False, False, False, False],
            "runs_on": [
                ["ubuntu-latest"],
                ["ubuntu-latest"],
                ["ubuntu-latest"],
                ["ubuntu-latest"],
                ["macos-latest"],
            ],
            "concurrency_set": [False, False, False, False, False],
            "has_ai_review": [False, False, False, True, False],
            "has_security_scan": [False, True, False, False, False],
        }
    )
    out = tmp_path / "processed" / "cicd.parquet"
    out.parent.mkdir(parents=True)
    df.write_parquet(out)
    return out


@pytest.fixture()
def empty_parquet(tmp_path: Path) -> Path:
    """Create an empty Parquet file with correct schema."""
    df = pl.DataFrame(
        schema={
            "repo": pl.Utf8,
            "workflow_name": pl.Utf8,
            "triggers": pl.List(pl.Utf8),
            "job_names": pl.List(pl.Utf8),
            "uses_matrix": pl.Boolean,
            "uses_reusable_workflows": pl.Boolean,
            "actions_used": pl.List(pl.Utf8),
            "actions_normalized": pl.List(pl.Utf8),
            "has_permissions_block": pl.Boolean,
            "runs_on": pl.List(pl.Utf8),
            "concurrency_set": pl.Boolean,
            "has_ai_review": pl.Boolean,
            "has_security_scan": pl.Boolean,
        }
    )
    out = tmp_path / "processed" / "cicd.parquet"
    out.parent.mkdir(parents=True)
    df.write_parquet(out)
    return out


def test_analyze_with_data(sample_parquet: Path, tmp_path: Path) -> None:
    """Analyze should produce results with data."""
    analysis_dir = tmp_path / "analysis"
    with (
        patch("src.analyzer.PARQUET_PATH", sample_parquet),
        patch("src.analyzer.ANALYSIS_DIR", analysis_dir),
        patch("src.analyzer.CURRENT_JSON", analysis_dir / "current.json"),
        patch("src.analyzer.PREVIOUS_JSON", analysis_dir / "previous.json"),
    ):
        results = analyze()

    assert results["total_repos"] == 3
    assert results["total_workflows"] == 5
    assert results["matrix_usage"]["matrix_repos"] >= 1
    assert len(results["popular_actions"]) > 0
    # actions/checkout should be the most popular
    assert results["popular_actions"][0]["action"] == "actions/checkout"


def test_analyze_empty_parquet(empty_parquet: Path, tmp_path: Path) -> None:
    """Analyze should return empty results for empty Parquet without crashing."""
    analysis_dir = tmp_path / "analysis"
    with (
        patch("src.analyzer.PARQUET_PATH", empty_parquet),
        patch("src.analyzer.ANALYSIS_DIR", analysis_dir),
        patch("src.analyzer.CURRENT_JSON", analysis_dir / "current.json"),
        patch("src.analyzer.PREVIOUS_JSON", analysis_dir / "previous.json"),
    ):
        results = analyze()

    assert results["total_repos"] == 0
    assert results["total_workflows"] == 0
    assert results["popular_actions"] == []


def test_analyze_missing_parquet(tmp_path: Path) -> None:
    """Analyze should return empty results when Parquet file doesn't exist."""
    analysis_dir = tmp_path / "analysis"
    with (
        patch("src.analyzer.PARQUET_PATH", tmp_path / "nonexistent.parquet"),
        patch("src.analyzer.ANALYSIS_DIR", analysis_dir),
        patch("src.analyzer.CURRENT_JSON", analysis_dir / "current.json"),
        patch("src.analyzer.PREVIOUS_JSON", analysis_dir / "previous.json"),
    ):
        results = analyze()

    assert results["total_repos"] == 0


def test_compute_diffs() -> None:
    """Diff should detect changes between runs."""
    current = {
        "total_repos": 5,
        "total_workflows": 10,
        "matrix_usage": {"percentage": 40.0},
        "permissions_usage": {"percentage": 20.0},
        "ai_review_adoption": {"count": 2},
    }
    previous = {
        "total_repos": 3,
        "total_workflows": 6,
        "matrix_usage": {"percentage": 33.0},
        "permissions_usage": {"percentage": 20.0},
        "ai_review_adoption": {"count": 0},
    }
    diffs = _compute_diffs(current, previous)
    assert len(diffs) > 0
    metrics = {d["metric"] for d in diffs}
    assert "total_repos" in metrics
    assert "ai_review_count" in metrics


def test_compute_diffs_no_changes() -> None:
    """No diffs when nothing changed."""
    data = {
        "total_repos": 3,
        "total_workflows": 6,
        "matrix_usage": {"percentage": 33.0},
        "permissions_usage": {"percentage": 20.0},
        "ai_review_adoption": {"count": 1},
    }
    diffs = _compute_diffs(data, data)
    assert diffs == []


def test_analyze_persists_results(sample_parquet: Path, tmp_path: Path) -> None:
    """Analyze should save current.json and previous.json."""
    analysis_dir = tmp_path / "analysis"
    current_json = analysis_dir / "current.json"
    previous_json = analysis_dir / "previous.json"
    with (
        patch("src.analyzer.PARQUET_PATH", sample_parquet),
        patch("src.analyzer.ANALYSIS_DIR", analysis_dir),
        patch("src.analyzer.CURRENT_JSON", current_json),
        patch("src.analyzer.PREVIOUS_JSON", previous_json),
    ):
        analyze()

    assert current_json.exists()
    assert previous_json.exists()
    data = json.loads(current_json.read_text())
    assert data["total_repos"] == 3
