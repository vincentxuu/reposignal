"""Seed-list versioning and trend comparison helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_seed_repos(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Seed repo file must contain a list")
    return data


def seed_repo_names(seeds: list[dict[str, Any]]) -> set[str]:
    return {
        f"{item['owner']}/{item['repo']}"
        for item in seeds
        if item.get("owner") and item.get("repo")
    }


def seed_fingerprint(seeds: list[dict[str, Any]]) -> str:
    names = sorted(seed_repo_names(seeds))
    digest = hashlib.sha256("\n".join(names).encode()).hexdigest()
    return digest[:16]


def seed_metadata(path: Path) -> dict[str, Any]:
    seeds = load_seed_repos(path)
    names = sorted(seed_repo_names(seeds))
    return {
        "seed_file": str(path),
        "repo_count": len(names),
        "fingerprint": seed_fingerprint(seeds),
        "repos": names,
    }


def comparison_intersection(previous: list[str], current: list[str]) -> dict[str, Any]:
    previous_set = set(previous)
    current_set = set(current)
    intersection = sorted(previous_set & current_set)
    return {
        "intersection_repos": intersection,
        "intersection_count": len(intersection),
        "previous_only": sorted(previous_set - current_set),
        "current_only": sorted(current_set - previous_set),
    }
