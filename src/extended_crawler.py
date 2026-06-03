"""Extended repo observation crawler for non-workflow engineering practices."""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from src.crawler import (
    CONCURRENCY,
    DATA_DIR,
    GITHUB_API,
    SEED_FILE,
    _headers,
    _request_with_retry,
)
from src.config_parsers import parse_batch2_file

logger = logging.getLogger(__name__)

CONFIGS_DIR = DATA_DIR / "configs"
BATCH1_OUTPUT = CONFIGS_DIR / "batch1.json"
BATCH2_OUTPUT = CONFIGS_DIR / "batch2.json"
BATCH3_OUTPUT = CONFIGS_DIR / "batch3.json"

BATCH1_OBSERVATIONS: dict[str, list[str]] = {
    "pre_commit": [".pre-commit-config.yaml", ".pre-commit-config.yml"],
    "codeowners": [".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"],
    "security_policy": ["SECURITY.md", ".github/SECURITY.md"],
    "contributing": ["CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"],
    "dependency_automation": [".github/dependabot.yml", ".github/dependabot.yaml", "renovate.json", ".github/renovate.json"],
    "pull_request_template": [".github/PULL_REQUEST_TEMPLATE.md", "PULL_REQUEST_TEMPLATE.md", ".github/PULL_REQUEST_TEMPLATE"],
    "issue_templates": [".github/ISSUE_TEMPLATE", ".github/ISSUE_TEMPLATE.md"],
}

BATCH2_PATHS = [
    "tsconfig.json",
    "pyproject.toml",
    "Cargo.toml",
    "turbo.json",
    "nx.json",
    "pnpm-workspace.yaml",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.yaml",
    ".eslintrc.yml",
    "eslint.config.js",
    "ruff.toml",
    ".ruff.toml",
    "biome.json",
    "biome.jsonc",
]

BATCH3_TARGETS: dict[str, list[dict[str, str]]] = {
    "release_strategy": [
        {"path": ".changeset", "type": "dir"},
        {"path": ".release-please-manifest.json", "type": "file"},
        {"path": "release-please-config.json", "type": "file"},
        {"path": "cliff.toml", "type": "file"},
        {"path": ".goreleaser.yml", "type": "file"},
        {"path": ".goreleaser.yaml", "type": "file"},
        {"path": "goreleaser.yml", "type": "file"},
        {"path": "goreleaser.yaml", "type": "file"},
    ],
    "dev_environment": [
        {"path": ".devcontainer", "type": "dir"},
        {"path": ".devcontainer/devcontainer.json", "type": "file"},
        {"path": "flake.nix", "type": "file"},
        {"path": "docker-compose.yml", "type": "file"},
        {"path": "docker-compose.yaml", "type": "file"},
        {"path": "compose.yml", "type": "file"},
        {"path": "compose.yaml", "type": "file"},
    ],
    "decision_records": [
        {"path": "docs/rfcs", "type": "dir"},
        {"path": "rfcs", "type": "dir"},
        {"path": "docs/adr", "type": "dir"},
        {"path": "docs/adrs", "type": "dir"},
        {"path": "adr", "type": "dir"},
        {"path": "adrs", "type": "dir"},
    ],
}


async def crawl_extended_batch1(seed_file: Path | None = None) -> dict[str, Any]:
    """Crawl high-value low-complexity repo files from the research Batch 1 list."""
    seed_file = seed_file or SEED_FILE
    repos = json.loads(seed_file.read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(CONCURRENCY)
    headers = _headers()
    stats = {
        "repos_total": len(repos),
        "repos_observed": 0,
        "requests": 0,
        "errors": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(headers=headers) as client:
        records = await asyncio.gather(*[
            _observe_repo_batch1(client, repo["owner"], repo["repo"], semaphore, stats)
            for repo in repos
        ])

    result = {
        "generated_at": stats["generated_at"],
        "batch": "extended-crawler-batch1",
        "observations": BATCH1_OBSERVATIONS,
        "stats": stats,
        "summary": summarize_batch1(records),
        "repos": records,
    }
    BATCH1_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BATCH1_OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote extended Batch 1 observations to %s", BATCH1_OUTPUT)
    return result


async def _observe_repo_batch1(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    semaphore: asyncio.Semaphore,
    stats: dict[str, Any],
) -> dict[str, Any]:
    record = {
        "repo": f"{owner}/{repo}",
        "url": f"https://github.com/{owner}/{repo}",
        "signals": {},
    }
    for signal, paths in BATCH1_OBSERVATIONS.items():
        found_paths = []
        for path in paths:
            stats["requests"] += 1
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
            resp = await _request_with_retry(client, url, semaphore=semaphore)
            if resp is None:
                stats["errors"] += 1
                continue
            if resp.status_code == 200:
                found_paths.append(path)
                break
            if resp.status_code == 404:
                continue
            stats["errors"] += 1
        record["signals"][signal] = {
            "present": bool(found_paths),
            "paths": found_paths,
        }
    stats["repos_observed"] += 1
    return record


def summarize_batch1(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Batch 1 file-presence coverage across repos."""
    total = len(records)
    signals = {}
    for signal in BATCH1_OBSERVATIONS:
        repos = [
            record["repo"]
            for record in records
            if record.get("signals", {}).get(signal, {}).get("present")
        ]
        signals[signal] = {
            "repo_count": len(repos),
            "adoption_pct": round(len(repos) / total * 100, 2) if total else 0.0,
            "repos": repos,
        }
    return {"total_repos": total, "signals": signals}


async def crawl_extended_batch2(seed_file: Path | None = None) -> dict[str, Any]:
    """Crawl and parse Batch 2 config files for trend analysis."""
    seed_file = seed_file or SEED_FILE
    repos = json.loads(seed_file.read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(CONCURRENCY)
    headers = _headers()
    stats = {
        "repos_total": len(repos),
        "repos_observed": 0,
        "files_found": 0,
        "parse_errors": 0,
        "requests": 0,
        "errors": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(headers=headers) as client:
        records = await asyncio.gather(*[
            _observe_repo_batch2(client, repo["owner"], repo["repo"], semaphore, stats)
            for repo in repos
        ])

    result = {
        "generated_at": stats["generated_at"],
        "batch": "extended-crawler-batch2",
        "paths": BATCH2_PATHS,
        "stats": stats,
        "summary": summarize_batch2(records),
        "repos": records,
    }
    BATCH2_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BATCH2_OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote extended Batch 2 observations to %s", BATCH2_OUTPUT)
    return result


async def _observe_repo_batch2(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    semaphore: asyncio.Semaphore,
    stats: dict[str, Any],
) -> dict[str, Any]:
    record = {"repo": f"{owner}/{repo}", "url": f"https://github.com/{owner}/{repo}", "files": []}
    for path in BATCH2_PATHS:
        stats["requests"] += 1
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        resp = await _request_with_retry(client, url, semaphore=semaphore)
        if resp is None:
            stats["errors"] += 1
            continue
        if resp.status_code == 404:
            continue
        if resp.status_code != 200:
            stats["errors"] += 1
            continue
        try:
            item = resp.json()
            if item.get("type") != "file":
                continue
            text = _decode_contents_api_file(item)
            parsed = parse_batch2_file(path, text)
            record["files"].append(parsed)
            stats["files_found"] += 1
        except Exception as exc:
            stats["parse_errors"] += 1
            record["files"].append({"kind": "parse_error", "path": path, "error": str(exc)})
    stats["repos_observed"] += 1
    return record


def summarize_batch2(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Batch 2 parsed config coverage and selected trend fields."""
    total = len(records)
    by_kind: dict[str, list[str]] = {}
    tsconfig_strict = 0
    pyproject_backends: dict[str, int] = {}
    cargo_workspaces = 0
    for record in records:
        repo = record["repo"]
        for file in record.get("files", []):
            kind = file.get("kind")
            if not kind or kind == "parse_error":
                continue
            by_kind.setdefault(kind, []).append(repo)
            parsed = file.get("parsed", {})
            if kind == "tsconfig" and parsed.get("strict") is True:
                tsconfig_strict += 1
            if kind == "pyproject" and parsed.get("build_backend"):
                backend = parsed["build_backend"]
                pyproject_backends[backend] = pyproject_backends.get(backend, 0) + 1
            if kind == "cargo" and parsed.get("workspace"):
                cargo_workspaces += 1
    return {
        "total_repos": total,
        "by_kind": {
            kind: {
                "repo_count": len(set(repos)),
                "adoption_pct": round(len(set(repos)) / total * 100, 2) if total else 0.0,
                "repos": sorted(set(repos)),
            }
            for kind, repos in sorted(by_kind.items())
        },
        "tsconfig_strict_repos": tsconfig_strict,
        "pyproject_build_backends": dict(sorted(pyproject_backends.items())),
        "cargo_workspace_repos": cargo_workspaces,
    }


async def crawl_extended_batch3(seed_file: Path | None = None) -> dict[str, Any]:
    """Crawl Batch 3 structure signals for release, dev environment, and RFC/ADR process."""
    seed_file = seed_file or SEED_FILE
    repos = json.loads(seed_file.read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(CONCURRENCY)
    headers = _headers()
    stats = {
        "repos_total": len(repos),
        "repos_observed": 0,
        "requests": 0,
        "errors": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    async with httpx.AsyncClient(headers=headers) as client:
        records = await asyncio.gather(*[
            _observe_repo_batch3(client, repo["owner"], repo["repo"], semaphore, stats)
            for repo in repos
        ])

    result = {
        "generated_at": stats["generated_at"],
        "batch": "extended-crawler-batch3",
        "targets": BATCH3_TARGETS,
        "stats": stats,
        "summary": summarize_batch3(records),
        "repos": records,
    }
    BATCH3_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    BATCH3_OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote extended Batch 3 observations to %s", BATCH3_OUTPUT)
    return result


async def _observe_repo_batch3(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    semaphore: asyncio.Semaphore,
    stats: dict[str, Any],
) -> dict[str, Any]:
    record = {"repo": f"{owner}/{repo}", "url": f"https://github.com/{owner}/{repo}", "signals": {}}
    for signal, targets in BATCH3_TARGETS.items():
        hits = []
        for target in targets:
            stats["requests"] += 1
            path = target["path"]
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
            resp = await _request_with_retry(client, url, semaphore=semaphore)
            if resp is None:
                stats["errors"] += 1
                continue
            if resp.status_code == 404:
                continue
            if resp.status_code != 200:
                stats["errors"] += 1
                continue
            inferred = _infer_batch3_hit(path, target["type"], resp)
            if inferred:
                hits.append(inferred)
        record["signals"][signal] = {
            "present": bool(hits),
            "hits": hits,
        }
    stats["repos_observed"] += 1
    return record


def summarize_batch3(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Batch 3 structural practice coverage."""
    total = len(records)
    signals = {}
    for signal in BATCH3_TARGETS:
        repos = [
            record["repo"]
            for record in records
            if record.get("signals", {}).get(signal, {}).get("present")
        ]
        signals[signal] = {
            "repo_count": len(repos),
            "adoption_pct": round(len(repos) / total * 100, 2) if total else 0.0,
            "repos": repos,
        }
    return {"total_repos": total, "signals": signals}


def _infer_batch3_hit(path: str, expected_type: str, resp: httpx.Response) -> dict[str, Any] | None:
    data = resp.json()
    if expected_type == "dir":
        if not isinstance(data, list):
            return None
        entries = [item.get("name") for item in data if isinstance(item, dict)]
        return {
            "path": path,
            "type": "dir",
            "entry_count": len(entries),
            "sample_entries": entries[:5],
        }
    if not isinstance(data, dict) or data.get("type") != "file":
        return None
    hit = {"path": path, "type": "file"}
    try:
        text = _decode_contents_api_file(data)
    except Exception:
        text = ""
    if "release-please" in path:
        hit["tool"] = "release-please"
    elif "goreleaser" in path:
        hit["tool"] = "goreleaser"
    elif path == "cliff.toml":
        hit["tool"] = "git-cliff"
    elif "devcontainer" in path:
        hit["tool"] = "devcontainer"
    elif path == "flake.nix":
        hit["tool"] = "nix"
    elif "compose" in path:
        hit["tool"] = "docker-compose"
    if text:
        hit["size"] = len(text)
    return hit


def _decode_contents_api_file(item: dict[str, Any]) -> str:
    content = item.get("content")
    if not isinstance(content, str):
        raise ValueError("Contents API response missing content")
    encoding = item.get("encoding")
    if encoding != "base64":
        raise ValueError(f"Unsupported content encoding: {encoding}")
    return base64.b64decode(content).decode("utf-8")


if __name__ == "__main__":
    print(json.dumps(asyncio.run(crawl_extended_batch1()), indent=2))
