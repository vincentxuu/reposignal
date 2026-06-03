"""Async crawler for GitHub Actions workflow files.

Loads seed_repos.json, fetches .github/workflows/ for each repo via GitHub
Contents API, downloads every YAML file, and saves raw copies to disk.
"""

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from src.seed_management import seed_metadata

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ERRORS_DIR = DATA_DIR / "errors"
CACHE_DIR = DATA_DIR / "cache"
HTTP_CACHE_FILE = CACHE_DIR / "http_metadata.json"
SEED_FILE = BASE_DIR / "seed_repos.json"

GITHUB_API = "https://api.github.com"
CONCURRENCY = 10
MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds
JITTER_MIN = 0.1
JITTER_MAX = 0.5
REQUEST_TIMEOUT = 30.0

logger = logging.getLogger("crawler")


def _setup_logging(run_date: str) -> None:
    """Configure logging to both stderr and an error log file."""
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = ERRORS_DIR / f"{run_date}.log"

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )

    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("GITHUB_TOKEN not set; requests will be severely rate-limited")
    return h


def _load_http_cache() -> dict[str, dict[str, str]]:
    if not HTTP_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(HTTP_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid HTTP cache metadata: %s", HTTP_CACHE_FILE)
        return {}


def _save_http_cache(cache: dict[str, dict[str, str]]) -> None:
    HTTP_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    HTTP_CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def _conditional_headers(cache: dict[str, dict[str, str]], url: str) -> dict[str, str]:
    entry = cache.get(url, {})
    headers = {}
    if entry.get("etag"):
        headers["If-None-Match"] = entry["etag"]
    if entry.get("last_modified"):
        headers["If-Modified-Since"] = entry["last_modified"]
    return headers


def _update_http_cache(cache: dict[str, dict[str, str]], url: str, resp: httpx.Response) -> None:
    etag = resp.headers.get("ETag")
    last_modified = resp.headers.get("Last-Modified")
    if etag or last_modified:
        cache[url] = {
            "etag": etag or cache.get(url, {}).get("etag", ""),
            "last_modified": last_modified or cache.get(url, {}).get("last_modified", ""),
        }


async def _request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    semaphore: asyncio.Semaphore,
    headers: dict[str, str] | None = None,
) -> httpx.Response | None:
    """GET with exponential backoff on 403/429 and timeout retry."""
    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            jitter = random.uniform(JITTER_MIN, JITTER_MAX)
            await asyncio.sleep(jitter)
            try:
                resp = await client.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
            except httpx.TimeoutException:
                logger.warning("Timeout attempt %d/%d: %s", attempt, MAX_RETRIES, url)
                if attempt == MAX_RETRIES:
                    logger.error("Timeout after %d retries, skipping: %s", MAX_RETRIES, url)
                    return None
                continue
            except httpx.HTTPError as exc:
                logger.error("HTTP error on %s: %s", url, exc)
                return None

            if resp.status_code in (200, 304):
                return resp
            if resp.status_code == 404:
                return resp  # caller handles 404 skip
            if resp.status_code in (403, 429):
                wait = BACKOFF_BASE**attempt + random.uniform(JITTER_MIN, JITTER_MAX)
                # Check for Retry-After header
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait = max(wait, float(retry_after))
                    except ValueError:
                        pass
                logger.warning(
                    "Rate limited (%d) attempt %d/%d, waiting %.1fs: %s",
                    resp.status_code, attempt, MAX_RETRIES, wait, url,
                )
                await asyncio.sleep(wait)
                if attempt == MAX_RETRIES:
                    logger.error("Rate limit not resolved after %d retries: %s", MAX_RETRIES, url)
                    return None
                continue
            # Other status codes
            logger.error("Unexpected status %d for %s", resp.status_code, url)
            return None
    return None


async def _crawl_repo(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    semaphore: asyncio.Semaphore,
    stats: dict,
    http_cache: dict[str, dict[str, str]] | None = None,
) -> None:
    """List and download workflow files for a single repo."""
    list_url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/.github/workflows"
    http_cache = http_cache if http_cache is not None else {}
    resp = await _request_with_retry(
        client,
        list_url,
        semaphore=semaphore,
        headers=_conditional_headers(http_cache, list_url),
    )

    if resp is None:
        stats["errors"] += 1
        return
    if resp.status_code == 304:
        logger.info("Workflow listing unchanged, using cached files: %s/%s", owner, repo)
        stats["repos_unchanged"] += 1
        return
    if resp.status_code == 404:
        logger.info("No workflows found, skipping: %s/%s", owner, repo)
        stats["skipped_404"] += 1
        return
    _update_http_cache(http_cache, list_url, resp)

    try:
        items = resp.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON from contents API: %s/%s", owner, repo)
        stats["errors"] += 1
        return

    if not isinstance(items, list):
        logger.error("Unexpected response (not a list) for %s/%s", owner, repo)
        stats["errors"] += 1
        return

    yaml_files = [
        f for f in items
        if f.get("type") == "file"
        and (f["name"].endswith(".yml") or f["name"].endswith(".yaml"))
    ]

    if not yaml_files:
        logger.info("No YAML workflow files in %s/%s", owner, repo)
        return

    repo_dir = RAW_DIR / owner / repo
    repo_dir.mkdir(parents=True, exist_ok=True)

    for file_info in yaml_files:
        download_url = file_info.get("download_url")
        if not download_url:
            logger.warning("No download_url for %s in %s/%s", file_info["name"], owner, repo)
            stats["errors"] += 1
            continue

        out_path = repo_dir / file_info["name"]
        if file_info.get("sha") and out_path.exists():
            cache_key = f"sha:{owner}/{repo}/{file_info['name']}"
            if http_cache.get(cache_key, {}).get("sha") == file_info["sha"]:
                stats["files_unchanged"] += 1
                continue

        dl_resp = await _request_with_retry(
            client,
            download_url,
            semaphore=semaphore,
            headers=_conditional_headers(http_cache, download_url),
        )
        if dl_resp is not None and dl_resp.status_code == 304 and out_path.exists():
            stats["files_unchanged"] += 1
            continue
        if dl_resp is None or dl_resp.status_code != 200:
            logger.error("Failed to download %s from %s/%s", file_info["name"], owner, repo)
            stats["errors"] += 1
            continue

        out_path.write_text(dl_resp.text, encoding="utf-8")
        _update_http_cache(http_cache, download_url, dl_resp)
        if file_info.get("sha"):
            http_cache[f"sha:{owner}/{repo}/{file_info['name']}"] = {"sha": file_info["sha"]}
        stats["files_downloaded"] += 1
        logger.debug("Saved %s", out_path)

    stats["repos_crawled"] += 1
    logger.info("Crawled %s/%s — %d files", owner, repo, len(yaml_files))


async def crawl(seed_file: Path | None = None) -> dict:
    """Main entry point. Returns stats dict."""
    seed_file = seed_file or SEED_FILE
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    _setup_logging(run_date)

    if not seed_file.exists():
        logger.error("Seed file not found: %s", seed_file)
        return {"error": f"Seed file not found: {seed_file}"}

    repos = json.loads(seed_file.read_text(encoding="utf-8"))
    logger.info("Loaded %d repos from %s", len(repos), seed_file)

    stats = {
        "repos_total": len(repos),
        "repos_crawled": 0,
        "files_downloaded": 0,
        "files_unchanged": 0,
        "repos_unchanged": 0,
        "skipped_404": 0,
        "errors": 0,
        "run_date": run_date,
        "seed": seed_metadata(seed_file),
    }

    semaphore = asyncio.Semaphore(CONCURRENCY)
    headers = _headers()
    http_cache = _load_http_cache()

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [
            _crawl_repo(client, r["owner"], r["repo"], semaphore, stats, http_cache)
            for r in repos
        ]
        await asyncio.gather(*tasks)
    _save_http_cache(http_cache)

    elapsed = time.time()
    logger.info(
        "Done. repos_crawled=%d files=%d unchanged_files=%d skipped_404=%d errors=%d",
        stats["repos_crawled"],
        stats["files_downloaded"],
        stats["files_unchanged"],
        stats["skipped_404"],
        stats["errors"],
    )
    return stats


if __name__ == "__main__":
    result = asyncio.run(crawl())
    print(json.dumps(result, indent=2))
