"""Repo profile generation from seed metadata and CI/CD analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
PROFILES_DIR = BASE_DIR / "data" / "profiles"


def generate_profiles(results: dict[str, Any], metadata_path: Path | None = None) -> list[dict[str, Any]]:
    """Generate one JSON profile per repo for downstream reports/site pages."""
    metadata = _load_metadata(metadata_path or BASE_DIR / "seed_repos_metadata.json")
    repo_meta = {
        f"{item.get('owner')}/{item.get('repo')}": item
        for item in metadata
        if item.get("owner") and item.get("repo")
    }

    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    profiles = []
    security_by_repo = {
        item["repo"]: item
        for item in results.get("security_posture", {}).get("scores", [])
    }
    for repo in results.get("repo_summaries", []):
        meta = repo_meta.get(repo["repo"], {})
        description = meta.get("description") or ""
        profile = {
            "repo": repo["repo"],
            "url": repo["url"],
            "description": description,
            "summary": _summary_from_description(description),
            "stars": meta.get("stars") or meta.get("stargazers_count"),
            "forks": meta.get("forks") or meta.get("forks_count"),
            "language": meta.get("language"),
            "license": meta.get("license"),
            "topics": meta.get("topics") or [],
            "pushed_at": meta.get("pushed_at"),
            "cicd": {
                "workflow_count": repo.get("workflow_count", 0),
                "patterns": repo.get("pattern_slugs", []),
                "security_score": security_by_repo.get(repo["repo"], {}).get("score"),
                "maturity_pct": repo.get("maturity_pct"),
            },
        }
        out = PROFILES_DIR / f"{repo['repo'].replace('/', '--')}.json"
        out.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        profiles.append(profile)
    return profiles


def _load_metadata(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("repos", "items", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _summary_from_description(description: str) -> str:
    if not description:
        return ""
    text = " ".join(description.split())
    return text if len(text) <= 240 else text[:237].rstrip() + "..."
