"""Tests for the GitHub Actions workflow crawler."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.crawler import MAX_RETRIES, _crawl_repo, _request_with_retry, crawl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, json_data=None, text: str = "", headers=None):
    """Build a fake httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


WORKFLOW_YAML = "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n"

CONTENTS_API_RESPONSE = [
    {
        "name": "ci.yml",
        "type": "file",
        "download_url": "https://raw.githubusercontent.com/octocat/hello/main/.github/workflows/ci.yml",
    },
    {
        "name": "release.yaml",
        "type": "file",
        "download_url": "https://raw.githubusercontent.com/octocat/hello/main/.github/workflows/release.yaml",
    },
    {
        "name": "README.md",
        "type": "file",
        "download_url": "https://raw.githubusercontent.com/octocat/hello/main/.github/workflows/README.md",
    },
]


# ---------------------------------------------------------------------------
# 1. Successful fetch — files saved to data/raw/{owner}/{repo}/
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_successful_fetch(tmp_path, monkeypatch):
    """Crawl a repo with two YAML workflow files; verify they are saved."""
    # Seed file
    seed = tmp_path / "seed_repos.json"
    seed.write_text(json.dumps([{"owner": "octocat", "repo": "hello"}]))

    # Redirect RAW_DIR so files land under tmp_path
    raw_dir = tmp_path / "data" / "raw"
    monkeypatch.setattr("src.crawler.RAW_DIR", raw_dir)
    monkeypatch.setattr("src.crawler.DATA_DIR", tmp_path / "data")
    monkeypatch.setattr("src.crawler.ERRORS_DIR", tmp_path / "data" / "errors")

    contents_resp = _make_response(200, json_data=CONTENTS_API_RESPONSE)
    download_resp = _make_response(200, text=WORKFLOW_YAML)

    async def fake_get(url, **kwargs):
        if "/contents/" in url:
            return contents_resp
        return download_resp

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=fake_get)

    with patch("src.crawler.httpx.AsyncClient") as MockClientCls:
        # Make AsyncClient usable as async context manager
        MockClientCls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClientCls.return_value.__aexit__ = AsyncMock(return_value=False)

        stats = await crawl(seed)

    assert stats["repos_crawled"] == 1
    assert stats["files_downloaded"] == 2  # ci.yml + release.yaml (README.md filtered)
    assert stats["skipped_404"] == 0
    assert stats["errors"] == 0

    # Files on disk
    assert (raw_dir / "octocat" / "hello" / "ci.yml").exists()
    assert (raw_dir / "octocat" / "hello" / "release.yaml").exists()
    assert not (raw_dir / "octocat" / "hello" / "README.md").exists()


# ---------------------------------------------------------------------------
# 2. 404 response — repo skipped, stats["skipped_404"] incremented
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_repo_404_skips(tmp_path, monkeypatch):
    """When contents API returns 404, repo is skipped."""
    monkeypatch.setattr("src.crawler.RAW_DIR", tmp_path / "data" / "raw")

    resp_404 = _make_response(404)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=resp_404)

    sem = asyncio.Semaphore(10)
    stats = {"repos_crawled": 0, "files_downloaded": 0, "skipped_404": 0, "errors": 0}

    await _crawl_repo(mock_client, "octocat", "gone-repo", sem, stats)

    assert stats["skipped_404"] == 1
    assert stats["repos_crawled"] == 0
    assert stats["errors"] == 0


# ---------------------------------------------------------------------------
# 3. 403 rate-limit — retries with backoff, then errors after MAX_RETRIES
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_with_retry_403_exhausts_retries(monkeypatch):
    """403 rate-limit triggers retries; after MAX_RETRIES, returns None."""
    # Speed up sleeps
    monkeypatch.setattr("src.crawler.BACKOFF_BASE", 0.001)
    monkeypatch.setattr("src.crawler.JITTER_MIN", 0.0)
    monkeypatch.setattr("src.crawler.JITTER_MAX", 0.001)

    resp_403 = _make_response(403, headers={})

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=resp_403)

    sem = asyncio.Semaphore(10)
    result = await _request_with_retry(mock_client, "https://api.github.com/test", semaphore=sem)

    assert result is None
    assert mock_client.get.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_crawl_repo_403_increments_errors(tmp_path, monkeypatch):
    """When _request_with_retry returns None due to 403, stats['errors'] goes up."""
    monkeypatch.setattr("src.crawler.RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr("src.crawler.BACKOFF_BASE", 0.001)
    monkeypatch.setattr("src.crawler.JITTER_MIN", 0.0)
    monkeypatch.setattr("src.crawler.JITTER_MAX", 0.001)

    resp_403 = _make_response(403, headers={})

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=resp_403)

    sem = asyncio.Semaphore(10)
    stats = {"repos_crawled": 0, "files_downloaded": 0, "skipped_404": 0, "errors": 0}

    await _crawl_repo(mock_client, "octocat", "ratelimited", sem, stats)

    assert stats["errors"] == 1
    assert stats["repos_crawled"] == 0


# ---------------------------------------------------------------------------
# 4. Network timeout — retries 3 times, then repo is skipped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_with_retry_timeout_returns_none(monkeypatch):
    """httpx.TimeoutException triggers retries; after MAX_RETRIES returns None."""
    monkeypatch.setattr("src.crawler.JITTER_MIN", 0.0)
    monkeypatch.setattr("src.crawler.JITTER_MAX", 0.001)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    sem = asyncio.Semaphore(10)
    result = await _request_with_retry(mock_client, "https://api.github.com/slow", semaphore=sem)

    assert result is None
    assert mock_client.get.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_crawl_repo_timeout_skips_repo(tmp_path, monkeypatch):
    """Timeout on contents API listing causes repo to be recorded as error."""
    monkeypatch.setattr("src.crawler.RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr("src.crawler.JITTER_MIN", 0.0)
    monkeypatch.setattr("src.crawler.JITTER_MAX", 0.001)

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    sem = asyncio.Semaphore(10)
    stats = {"repos_crawled": 0, "files_downloaded": 0, "skipped_404": 0, "errors": 0}

    await _crawl_repo(mock_client, "octocat", "slow-repo", sem, stats)

    assert stats["errors"] == 1
    assert stats["repos_crawled"] == 0
    assert stats["files_downloaded"] == 0
