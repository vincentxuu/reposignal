"""Build seed_repos.json from research markdown + GitHub Search API.

Every repo must pass validation before entering the seed list:
- Has .github/workflows/ with >= 2 YAML files
- Not archived
- Has a programming language (not a docs/list repo)
- Not in the skip list (awesome lists, education, non-code)
"""

import json
import logging
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SEEDS_DIR = BASE_DIR / "data" / "seeds"
RESEARCH_MD = Path.home() / "Projects" / "github-actions-workflow-research.md"
# Version-controlled list of repos always merged on top of the auto-built
# baseline. This is the "keep adding beyond the 200" mechanism: append entries
# here and they grow the analyzed universe (still validated, never dropped by
# TARGET_COUNT).
EXTRA_REPOS_FILE = SEEDS_DIR / "extra_repos.json"
TARGET_COUNT = 200

GITHUB_API = "https://api.github.com"
SEARCH_RATE_LIMIT_PAUSE = 2.5
MIN_WORKFLOW_FILES = 2

RUN_TS = time.strftime("%Y%m%d-%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("build_seed_list")

# Pattern: [owner/repo](https://github.com/owner/repo)
REPO_LINK_RE = re.compile(
    r"\[([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)\]\(https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\)"
)

# Keywords that indicate non-code repos (checked against topics + description)
SKIP_KEYWORDS = {
    "awesome-list", "awesome", "curated-list", "list", "lists",
    "interview", "interview-questions", "coding-interview",
    "tutorial", "tutorials", "education", "learning",
    "roadmap", "cheatsheet", "cheatsheets",
    "cookbook", "recipes", "cooking",
    "books", "book", "book-series", "free-programming-books",
    "prompts", "prompt-engineering",
}

# Repos to always skip (known non-code)
SKIP_REPOS = {
    "996icu/996.ICU",
    "Anduin2017/HowToCook",
    "goldbergyoni/nodebestpractices",
    "justjavac/free-programming-books-zh_CN",
    "getify/You-Dont-Know-JS",
    "obra/superpowers",
}


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    else:
        logger.warning("GITHUB_TOKEN not set; requests will be severely rate-limited")
    return h


def _extract_metadata(item: dict) -> dict:
    """Extract useful metadata fields from a GitHub API repo object."""
    return {
        "full_name": item.get("full_name", ""),
        "description": (item.get("description") or "")[:200],
        "language": item.get("language") or "",
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "open_issues": item.get("open_issues_count", 0),
        "topics": item.get("topics", []),
        "license": (item.get("license") or {}).get("spdx_id", ""),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "pushed_at": item.get("pushed_at", ""),
        "archived": item.get("archived", False),
        "default_branch": item.get("default_branch", "main"),
    }


def _is_skip_by_content(meta: dict) -> str | None:
    """Check if repo should be skipped based on metadata. Returns reason or None."""
    full_name = meta.get("full_name", "")

    # Hardcoded skip list
    if full_name in SKIP_REPOS:
        return f"in skip list"

    # Archived
    if meta.get("archived"):
        return "archived"

    # No programming language = likely docs/list repo
    if not meta.get("language"):
        return "no programming language"

    # Check topics for skip keywords
    topics = set(t.lower() for t in meta.get("topics", []))
    matches = topics & SKIP_KEYWORDS
    if matches:
        # Some repos have 'awesome' topic but are real code projects, check more carefully
        desc = (meta.get("description") or "").lower()
        is_likely_list = (
            "awesome" in full_name.lower()
            or any(w in desc for w in ["curated list", "collection of", "list of"])
            or not meta.get("language")  # no language = definitely a list
        )
        if is_likely_list:
            return f"skip keywords in topics: {matches}"

    # Check description for skip keywords
    desc = (meta.get("description") or "").lower()
    for kw in ["curated list", "awesome list", "collection of resources",
               "interview prep", "coding interview", "cookbook", "recipes"]:
        if kw in desc:
            return f"skip keyword in description: '{kw}'"

    return None


def _check_workflows(client: httpx.Client, full_name: str) -> int:
    """Check how many workflow YAML files a repo has. Returns count (0 if none)."""
    try:
        resp = client.get(f"{GITHUB_API}/repos/{full_name}/contents/.github/workflows")
        if resp.status_code != 200:
            return 0
        items = resp.json()
        if not isinstance(items, list):
            return 0
        return sum(
            1 for f in items
            if isinstance(f, dict)
            and (f.get("name", "").endswith(".yml") or f.get("name", "").endswith(".yaml"))
        )
    except Exception:
        return 0


def validate_repo(
    client: httpx.Client,
    full_name: str,
    *,
    source: str,
) -> tuple[dict | None, str | None]:
    """Validate a single repo. Returns (metadata, skip_reason).

    If skip_reason is None, the repo passed validation.
    """
    # Fetch repo metadata
    try:
        resp = client.get(f"{GITHUB_API}/repos/{full_name}")
        if resp.status_code == 404:
            return None, "not found on GitHub"
        if resp.status_code in (403, 429):
            wait = int(resp.headers.get("Retry-After", "60"))
            logger.warning("Rate limited on %s, waiting %ds", full_name, wait)
            time.sleep(wait)
            resp = client.get(f"{GITHUB_API}/repos/{full_name}")
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return None, "timeout"

    meta = _extract_metadata(resp.json())
    meta["source"] = source

    # Content-based filtering
    skip_reason = _is_skip_by_content(meta)
    if skip_reason:
        return meta, skip_reason

    # Check for workflow files
    wf_count = _check_workflows(client, full_name)
    meta["workflow_count"] = wf_count

    if wf_count == 0:
        return meta, "no .github/workflows/"
    if wf_count < MIN_WORKFLOW_FILES:
        return meta, f"only {wf_count} workflow file (minimum {MIN_WORKFLOW_FILES})"

    return meta, None  # passed!


def parse_research_md(md_path: Path) -> list[dict[str, str]]:
    """Extract unique {owner, repo} dicts from markdown table rows."""
    if not md_path.exists():
        logger.warning("Research markdown not found: %s", md_path)
        return []

    text = md_path.read_text(encoding="utf-8")
    seen: set[str] = set()
    repos: list[dict[str, str]] = []

    for match in REPO_LINK_RE.finditer(text):
        full_name = match.group(1)
        if full_name in seen:
            continue
        seen.add(full_name)
        owner, repo = full_name.split("/", 1)
        repos.append({"owner": owner, "repo": repo})

    logger.info("Parsed %d repos from %s", len(repos), md_path)
    return repos


def load_extra_repos(path: Path) -> list[dict[str, str]]:
    """Load the version-controlled extra-repo list (always-included additions)."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Could not parse %s; ignoring extras", path)
        return []
    repos: list[dict[str, str]] = []
    for item in data:
        if isinstance(item, dict) and item.get("owner") and item.get("repo"):
            repos.append({"owner": item["owner"], "repo": item["repo"]})
    return repos


def merge_extra_repos(extras, accepted, accepted_set, all_metadata, skipped, *, validate):
    """Append validated extra repos on top of the baseline (beyond TARGET_COUNT).

    Each extra is still validated; failures are logged + skipped (never crawled
    blind), but a passing extra is never dropped by the cap. Mutates accepted /
    all_metadata / skipped in place. Returns accepted.
    """
    for r in extras:
        full_name = f"{r['owner']}/{r['repo']}"
        if full_name in accepted_set:
            logger.debug("Extra %s already in baseline; skipping duplicate", full_name)
            continue
        meta, skip_reason = validate(full_name)
        if meta:
            all_metadata[full_name] = meta
        if skip_reason:
            logger.warning("SKIP [manual] %s — %s", full_name, skip_reason)
            skipped.append({"repo": full_name, "source": "manual", "reason": skip_reason})
        else:
            accepted.append({"owner": r["owner"], "repo": r["repo"]})
            accepted_set.add(full_name)
            logger.info("KEEP [manual] %s", full_name)
    return accepted


def build_seed_list() -> list[dict[str, str]]:
    """Build the seed list with validation on every repo."""
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    # Parse candidates from research markdown
    candidates = parse_research_md(RESEARCH_MD)
    logger.info("Validating %d repos from research file...", len(candidates))

    headers = _headers()
    accepted: list[dict[str, str]] = []
    all_metadata: dict[str, dict] = {}
    skipped: list[dict] = []
    accepted_set: set[str] = set()

    with httpx.Client(headers=headers, timeout=30.0) as client:
        # Validate research repos
        for i, r in enumerate(candidates):
            full_name = f"{r['owner']}/{r['repo']}"
            meta, skip_reason = validate_repo(client, full_name, source="research")

            if meta:
                all_metadata[full_name] = meta

            if skip_reason:
                logger.info("SKIP [research] %s — %s", full_name, skip_reason)
                skipped.append({"repo": full_name, "source": "research", "reason": skip_reason})
            else:
                accepted.append(r)
                accepted_set.add(full_name)
                logger.debug("KEEP [research] %s", full_name)

            if (i + 1) % 20 == 0:
                logger.info("Progress: %d/%d research repos validated, %d accepted",
                            i + 1, len(candidates), len(accepted))

        logger.info("Research repos: %d accepted, %d skipped", len(accepted), len(skipped))

        # Fill from Search API if needed
        if len(accepted) < TARGET_COUNT:
            needed = TARGET_COUNT - len(accepted)
            logger.info("Need %d more repos from Search API...", needed)
            page = 1

            while len(accepted) < TARGET_COUNT:
                resp = client.get(
                    f"{GITHUB_API}/search/repositories",
                    params={"q": "stars:>5000", "sort": "stars", "order": "desc",
                            "per_page": 100, "page": page},
                )

                if resp.status_code in (403, 429):
                    wait = int(resp.headers.get("Retry-After", "60"))
                    logger.warning("Search rate limited, waiting %ds", wait)
                    time.sleep(wait)
                    continue

                if resp.status_code != 200:
                    logger.error("Search API returned %d", resp.status_code)
                    break

                items = resp.json().get("items", [])
                if not items:
                    break

                for item in items:
                    full_name = item["full_name"]
                    if full_name in accepted_set:
                        continue

                    # Quick pre-filter from search result (no extra API call)
                    if not item.get("language"):
                        continue
                    if item.get("archived"):
                        continue

                    meta, skip_reason = validate_repo(client, full_name, source="search")
                    if meta:
                        all_metadata[full_name] = meta

                    if skip_reason:
                        logger.debug("SKIP [search] %s — %s", full_name, skip_reason)
                        skipped.append({"repo": full_name, "source": "search", "reason": skip_reason})
                    else:
                        owner, repo = full_name.split("/", 1)
                        accepted.append({"owner": owner, "repo": repo})
                        accepted_set.add(full_name)
                        logger.info("KEEP [search] %s (%d stars, %d workflows)",
                                    full_name, meta.get("stars", 0), meta.get("workflow_count", 0))

                    if len(accepted) >= TARGET_COUNT:
                        break

                page += 1
                time.sleep(SEARCH_RATE_LIMIT_PAUSE)
                if page > 10:
                    break

        # Always merge the version-controlled extra-repo list on top of the
        # baseline — the "keep adding beyond the auto 200" mechanism.
        extras = load_extra_repos(EXTRA_REPOS_FILE)
        if extras:
            logger.info("Merging %d extra (manually pinned) repos on top of baseline...", len(extras))
            merge_extra_repos(
                extras, accepted, accepted_set, all_metadata, skipped,
                validate=lambda full_name: validate_repo(client, full_name, source="manual"),
            )

    logger.info("Final: %d accepted, %d skipped", len(accepted), len(skipped))

    # Write timestamped seed list
    seed_file = SEEDS_DIR / f"seed_repos-{RUN_TS}.json"
    seed_file.write_text(json.dumps(accepted, indent=2, ensure_ascii=False) + "\n")
    logger.info("Wrote %s", seed_file)

    # Write timestamped metadata
    meta_file = SEEDS_DIR / f"metadata-{RUN_TS}.json"
    meta_file.write_text(json.dumps(all_metadata, indent=2, ensure_ascii=False) + "\n")

    # Write skip log (for review)
    skip_file = SEEDS_DIR / f"skipped-{RUN_TS}.json"
    skip_file.write_text(json.dumps(skipped, indent=2, ensure_ascii=False) + "\n")
    logger.info("Wrote skip log: %s (%d repos)", skip_file, len(skipped))

    # Update symlinks
    latest_seed = BASE_DIR / "seed_repos.json"
    latest_seed.unlink(missing_ok=True)
    latest_seed.symlink_to(seed_file.relative_to(BASE_DIR))

    latest_meta = SEEDS_DIR / "metadata-latest.json"
    latest_meta.unlink(missing_ok=True)
    latest_meta.symlink_to(meta_file.name)

    logger.info("Updated symlinks: seed_repos.json -> %s", seed_file.name)
    return accepted


if __name__ == "__main__":
    result = build_seed_list()
    print(f"\nGenerated seed_repos.json with {len(result)} repos")
