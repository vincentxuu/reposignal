"""Tests for extended repository observation crawling."""

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from src.extended_crawler import (
    _observe_repo_batch1,
    summarize_batch1,
    summarize_batch2,
    summarize_batch3,
)


def _response(status_code: int):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    return resp


def test_summarize_batch1_counts_signal_adoption() -> None:
    records = [
        {
            "repo": "a/one",
            "signals": {
                "security_policy": {"present": True, "paths": ["SECURITY.md"]},
                "codeowners": {"present": False, "paths": []},
            },
        },
        {
            "repo": "b/two",
            "signals": {
                "security_policy": {"present": False, "paths": []},
                "codeowners": {"present": True, "paths": ["CODEOWNERS"]},
            },
        },
    ]

    summary = summarize_batch1(records)

    assert summary["total_repos"] == 2
    assert summary["signals"]["security_policy"]["repo_count"] == 1
    assert summary["signals"]["security_policy"]["adoption_pct"] == 50.0
    assert summary["signals"]["codeowners"]["repos"] == ["b/two"]


@pytest.mark.asyncio
async def test_observe_repo_batch1_records_present_paths(monkeypatch) -> None:
    async def fake_request(client, url, *, semaphore):
        if url.endswith("/SECURITY.md") or url.endswith("/.github/CODEOWNERS"):
            return _response(200)
        return _response(404)

    monkeypatch.setattr("src.extended_crawler._request_with_retry", fake_request)
    stats = {"requests": 0, "errors": 0, "repos_observed": 0}

    record = await _observe_repo_batch1(
        client=MagicMock(spec=httpx.AsyncClient),
        owner="octo",
        repo="repo",
        semaphore=asyncio.Semaphore(10),
        stats=stats,
    )

    assert record["repo"] == "octo/repo"
    assert record["signals"]["security_policy"]["present"] is True
    assert record["signals"]["security_policy"]["paths"] == ["SECURITY.md"]
    assert record["signals"]["codeowners"]["paths"] == [".github/CODEOWNERS"]
    assert stats["repos_observed"] == 1
    assert stats["errors"] == 0


def test_summarize_batch2_aggregates_config_trends() -> None:
    records = [
        {
            "repo": "a/ts",
            "files": [
                {"kind": "tsconfig", "path": "tsconfig.json", "parsed": {"strict": True}},
                {"kind": "pyproject", "path": "pyproject.toml", "parsed": {"build_backend": "hatchling.build"}},
            ],
        },
        {
            "repo": "b/rust",
            "files": [
                {"kind": "cargo", "path": "Cargo.toml", "parsed": {"workspace": True}},
            ],
        },
    ]

    summary = summarize_batch2(records)

    assert summary["by_kind"]["tsconfig"]["repo_count"] == 1
    assert summary["tsconfig_strict_repos"] == 1
    assert summary["pyproject_build_backends"] == {"hatchling.build": 1}
    assert summary["cargo_workspace_repos"] == 1


def test_summarize_batch3_counts_structural_signals() -> None:
    records = [
        {
            "repo": "a/release",
            "signals": {
                "release_strategy": {"present": True, "hits": [{"path": ".changeset"}]},
                "dev_environment": {"present": True, "hits": [{"path": ".devcontainer"}]},
                "decision_records": {"present": False, "hits": []},
            },
        },
        {
            "repo": "b/adr",
            "signals": {
                "release_strategy": {"present": False, "hits": []},
                "dev_environment": {"present": False, "hits": []},
                "decision_records": {"present": True, "hits": [{"path": "docs/adr"}]},
            },
        },
    ]

    summary = summarize_batch3(records)

    assert summary["signals"]["release_strategy"]["repo_count"] == 1
    assert summary["signals"]["dev_environment"]["adoption_pct"] == 50.0
    assert summary["signals"]["decision_records"]["repos"] == ["b/adr"]
