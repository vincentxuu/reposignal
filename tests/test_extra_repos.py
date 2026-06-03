"""Tests for the extra-repo merge mechanism (adding repos beyond the baseline)."""

import json
from pathlib import Path

from src.scripts.build_seed_list import load_extra_repos, merge_extra_repos


def _passing_validator(full_name):
    return {"full_name": full_name, "workflow_count": 3}, None


def _failing_validator(full_name):
    return {"full_name": full_name, "workflow_count": 0}, "no .github/workflows/"


def test_load_extra_repos_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_extra_repos(tmp_path / "nope.json") == []


def test_load_extra_repos_filters_malformed_entries(tmp_path: Path) -> None:
    f = tmp_path / "extra.json"
    f.write_text(json.dumps([
        {"owner": "a", "repo": "b"},
        {"owner": "a"},          # missing repo
        {"repo": "b"},           # missing owner
        "not-a-dict",
    ]))
    assert load_extra_repos(f) == [{"owner": "a", "repo": "b"}]


def test_merge_appends_beyond_baseline() -> None:
    accepted = [{"owner": "x", "repo": str(i)} for i in range(200)]
    accepted_set = {f"x/{i}" for i in range(200)}
    skipped: list[dict] = []
    metadata: dict[str, dict] = {}

    merge_extra_repos(
        [{"owner": "new", "repo": "repo"}],
        accepted, accepted_set, metadata, skipped,
        validate=_passing_validator,
    )

    # Grows past the 200 cap.
    assert len(accepted) == 201
    assert {"owner": "new", "repo": "repo"} in accepted
    assert "new/repo" in metadata
    assert skipped == []


def test_merge_skips_failing_validation_but_records_reason() -> None:
    accepted: list[dict] = []
    accepted_set: set[str] = set()
    skipped: list[dict] = []
    metadata: dict[str, dict] = {}

    merge_extra_repos(
        [{"owner": "empty", "repo": "repo"}],
        accepted, accepted_set, metadata, skipped,
        validate=_failing_validator,
    )

    assert accepted == []  # not crawled blind
    assert skipped == [{"repo": "empty/repo", "source": "manual", "reason": "no .github/workflows/"}]


def test_merge_dedupes_against_baseline() -> None:
    accepted = [{"owner": "dup", "repo": "repo"}]
    accepted_set = {"dup/repo"}
    skipped: list[dict] = []
    metadata: dict[str, dict] = {}

    merge_extra_repos(
        [{"owner": "dup", "repo": "repo"}],
        accepted, accepted_set, metadata, skipped,
        validate=_passing_validator,
    )

    assert len(accepted) == 1  # no duplicate added
