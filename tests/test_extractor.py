"""Tests for the CI/CD workflow extractor."""

from pathlib import Path
import shutil

import polars as pl
import pytest

from src.extractors.cicd import CICDExtractor

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def extractor() -> CICDExtractor:
    return CICDExtractor()


@pytest.fixture()
def raw_dir(tmp_path: Path) -> Path:
    """Set up a fake data/raw/test-owner/test-repo/ tree (flat, matching crawler output)."""
    repo_dir = tmp_path / "test-owner" / "test-repo"
    repo_dir.mkdir(parents=True)
    for yml in FIXTURES.glob("*.yml"):
        shutil.copy(yml, repo_dir / yml.name)
    return tmp_path


def test_normal_workflow_parsing(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "normal_workflow")

    assert len(row) == 1
    r = row.row(0, named=True)
    assert r["repo"] == "test-owner/test-repo"
    assert "push" in r["triggers"]
    assert "pull_request" in r["triggers"]
    assert r["has_permissions_block"] is True


def test_matrix_detection(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "matrix_workflow")

    assert len(row) >= 1
    assert row["uses_matrix"][0] is True


def test_ai_review_detection(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "ai_review_workflow")

    assert len(row) == 1
    assert row["has_ai_review"][0] is True


def test_security_scan_detection(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "security_workflow")

    assert len(row) == 1
    assert row["has_security_scan"][0] is True


def test_malformed_yaml_skipped(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    # malformed.yml should not produce a valid row
    broken = df.filter(pl.col("workflow_name") == "Broken")
    assert len(broken) == 0


def test_empty_file_skipped(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    assert isinstance(df, pl.DataFrame)


def test_minimal_yaml_defaults(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "minimal")

    assert len(row) == 1
    r = row.row(0, named=True)
    assert r["uses_matrix"] is False
    assert r["has_ai_review"] is False
    assert r["has_security_scan"] is False


def test_permissions_detection(extractor: CICDExtractor, raw_dir: Path) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "normal_workflow")

    assert len(row) == 1
    assert row["has_permissions_block"][0] is True


def test_actions_normalized_strips_version(
    extractor: CICDExtractor, raw_dir: Path
) -> None:
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "normal_workflow")

    assert len(row) == 1
    actions_norm = row["actions_normalized"][0].to_list()
    assert "actions/checkout" in actions_norm
    assert all("@" not in a for a in actions_norm)


# ------------------------------------------------------------------
# Edge case tests
# ------------------------------------------------------------------


def test_on_boolean_triggers(extractor: CICDExtractor, raw_dir: Path) -> None:
    """When PyYAML parses `on: true`, triggers should be an empty list."""
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "on_boolean")

    assert len(row) == 1
    triggers = row["triggers"][0].to_list()
    assert triggers == []


def test_sha_version_normalized(extractor: CICDExtractor, raw_dir: Path) -> None:
    """All @suffixes (SHA, semver, branch) should be stripped in actions_normalized."""
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "sha_versions")

    assert len(row) == 1
    actions_used = row["actions_used"][0].to_list()
    actions_norm = row["actions_normalized"][0].to_list()

    # Raw actions retain their version suffixes
    assert "actions/checkout@abc123def456" in actions_used
    assert "actions/setup-python@v5" in actions_used
    assert "custom/action@main" in actions_used

    # Normalized actions have all @suffixes stripped
    assert "actions/checkout" in actions_norm
    assert "actions/setup-python" in actions_norm
    assert "custom/action" in actions_norm
    assert all("@" not in a for a in actions_norm)


def test_composite_action_in_actions_used(
    extractor: CICDExtractor, raw_dir: Path
) -> None:
    """Local path actions (e.g. ./.github/actions/foo) should appear in actions_used."""
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "composite_action")

    assert len(row) == 1
    actions_used = row["actions_used"][0].to_list()
    assert "./.github/actions/foo" in actions_used


def test_many_jobs_handled(extractor: CICDExtractor, raw_dir: Path) -> None:
    """A workflow with 20 jobs should be fully parsed with all job names present."""
    df = extractor.extract(raw_dir)
    row = df.filter(pl.col("workflow_name") == "many_jobs")

    assert len(row) == 1
    job_names = row["job_names"][0].to_list()
    assert len(job_names) == 20
    for i in range(1, 21):
        assert f"job-{i:02d}" in job_names
