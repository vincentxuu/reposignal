"""Enricher module — fetches action.yml descriptions from GitHub API.

Given a list of action names (e.g. "actions/checkout"), fetches the
action.yml (or action.yaml) from each repo and extracts the description.
Results are cached to data/cache/action_descriptions.json to avoid
redundant API calls across runs.
"""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

import re

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "action_descriptions.json"
AI_REVIEW_CACHE_FILE = CACHE_DIR / "ai_review_actions.json"
GITHUB_API = "https://api.github.com"
CONCURRENCY = 10

# Keywords to detect AI review actions from action.yml descriptions
AI_REVIEW_DESC_PATTERNS = re.compile(
    r"(ai|llm|gpt|claude|copilot|gemini).{0,30}(review|pr\b|pull.request)"
    r"|"
    r"(review|pr\b|pull.request).{0,30}(ai|llm|gpt|claude|copilot|gemini)"
    r"|"
    r"code.review.{0,20}(ai|automat|intelligen)"
    r"|"
    r"(ai|automat|intelligen).{0,20}code.review",
    re.IGNORECASE,
)


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _load_cache() -> dict[str, str]:
    """Load cached descriptions from disk."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    """Persist cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


async def _fetch_action_description(
    client: httpx.AsyncClient,
    action: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str, str]:
    """Fetch description from action.yml/action.yaml for a single action.

    Returns (action_name, description). Description is "" on failure.
    """
    # Skip local actions like ./.github/actions/foo
    if action.startswith("."):
        return (action, "")

    # Extract owner/repo (action might be owner/repo/subpath)
    parts = action.split("/")
    if len(parts) < 2:
        return (action, "")
    owner_repo = f"{parts[0]}/{parts[1]}"

    async with semaphore:
        for filename in ["action.yml", "action.yaml"]:
            # If action has subpath (e.g. github/codeql-action/analyze),
            # look for action.yml in that subpath
            if len(parts) > 2:
                subpath = "/".join(parts[2:])
                path = f"{subpath}/{filename}"
            else:
                path = filename

            url = f"{GITHUB_API}/repos/{owner_repo}/contents/{path}"
            try:
                resp = await client.get(url, timeout=15.0)
            except httpx.HTTPError:
                continue

            if resp.status_code != 200:
                continue

            try:
                data = resp.json()
                content = base64.b64decode(data["content"]).decode()
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    desc = parsed.get("description", "")
                    if desc:
                        return (action, str(desc))
            except Exception:
                continue

    return (action, "")


async def fetch_action_descriptions(actions: list[str]) -> dict[str, str]:
    """Fetch descriptions for a list of actions, using cache.

    Args:
        actions: List of action names (e.g. ["actions/checkout", "docker/login-action"])

    Returns:
        Dict mapping action name → description string.
    """
    cache = _load_cache()

    # Find which actions need fetching
    to_fetch = [a for a in actions if a not in cache and not a.startswith(".")]

    if to_fetch:
        logger.info("Fetching action.yml descriptions for %d actions (%d cached)",
                     len(to_fetch), len(actions) - len(to_fetch))
        semaphore = asyncio.Semaphore(CONCURRENCY)
        headers = _headers()

        async with httpx.AsyncClient(headers=headers) as client:
            tasks = [
                _fetch_action_description(client, action, semaphore)
                for action in to_fetch
            ]
            results = await asyncio.gather(*tasks)

        for action, desc in results:
            cache[action] = desc

        _save_cache(cache)
        logger.info("Cached %d action descriptions", len(cache))
    else:
        logger.info("All %d action descriptions found in cache", len(actions))

    return {a: cache.get(a, "") for a in actions}


# ------------------------------------------------------------------
# AI Review action discovery
# ------------------------------------------------------------------

async def discover_ai_review_actions(min_stars: int = 3) -> set[str]:
    """Discover AI code review actions from two sources:

    1. GitHub Search API: repos matching "ai code review" with github-actions topic
    2. Cached action.yml descriptions: keyword matching for AI + review patterns

    Results are cached to data/cache/ai_review_actions.json.
    Returns a set of action names (owner/repo format).
    """
    # Load existing cache
    cached: dict[str, list[str]] = {}
    if AI_REVIEW_CACHE_FILE.exists():
        try:
            cached = json.loads(AI_REVIEW_CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    # Source 1: GitHub Search API
    search_results: set[str] = set()
    headers = _headers()
    queries = [
        "topic:github-actions ai code review",
        "topic:github-actions ai pr review",
        "topic:github-actions llm code review",
    ]

    async with httpx.AsyncClient(headers=headers) as client:
        for query in queries:
            try:
                resp = await client.get(
                    f"{GITHUB_API}/search/repositories",
                    params={"q": query, "sort": "stars", "per_page": 50},
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        if item.get("stargazers_count", 0) >= min_stars:
                            search_results.add(item["full_name"])
            except httpx.HTTPError as exc:
                logger.warning("Search API error for %r: %s", query, exc)

    # Also add well-known actions that might not appear in search
    well_known = {
        "anthropics/claude-code-action",
        "coderabbitai/ai-pr-reviewer",
    }
    search_results.update(well_known)

    logger.info("GitHub Search found %d AI review action candidates", len(search_results))

    # Source 2: scan cached action.yml descriptions
    desc_cache = _load_cache()
    desc_matches: set[str] = set()
    for action, desc in desc_cache.items():
        if desc and AI_REVIEW_DESC_PATTERNS.search(desc):
            desc_matches.add(action)

    logger.info("Description scan found %d AI review action candidates", len(desc_matches))

    # Union of both sources
    all_ai_actions = search_results | desc_matches

    # Save cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_data = {
        "from_search": sorted(search_results),
        "from_descriptions": sorted(desc_matches),
        "combined": sorted(all_ai_actions),
    }
    AI_REVIEW_CACHE_FILE.write_text(json.dumps(cache_data, indent=2))
    logger.info("Total AI review actions discovered: %d", len(all_ai_actions))

    return all_ai_actions
