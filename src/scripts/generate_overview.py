"""Generate a readable overview of seed repos from existing metadata.

Reads metadata JSON (already fetched by build_seed_list.py), no API calls needed.
"""

import json
import logging
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SEEDS_DIR = BASE_DIR / "data" / "seeds"

RUN_TS = time.strftime("%Y%m%d-%H%M%S")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("generate_overview")


def _find_latest_metadata() -> Path | None:
    """Find the most recent metadata file in data/seeds/."""
    # Try symlink first
    latest = SEEDS_DIR / "metadata-latest.json"
    if latest.exists():
        return latest

    # Fallback: find newest metadata file
    candidates = sorted(SEEDS_DIR.glob("*metadata*.json"), reverse=True)
    return candidates[0] if candidates else None


def categorize(meta: dict) -> str:
    """Guess a category from language, topics, and description."""
    topics = set(t.lower() for t in meta.get("topics", []))
    desc = (meta.get("description") or "").lower()

    if topics & {"awesome", "awesome-list", "list", "lists"}:
        return "Awesome List"
    if topics & {"machine-learning", "deep-learning", "ai", "llm", "artificial-intelligence", "nlp", "gpt", "chatgpt", "langchain"}:
        return "AI / ML"
    if topics & {"devops", "ci-cd", "docker", "kubernetes", "infrastructure", "terraform"}:
        return "DevOps / Infra"
    if topics & {"database", "sql", "nosql"}:
        return "Database"
    if topics & {"security", "hacking", "penetration-testing", "vulnerability"}:
        return "Security"
    if topics & {"frontend", "react", "vue", "angular", "svelte", "css", "ui"}:
        return "Frontend"
    if topics & {"backend", "api", "rest", "graphql", "web-framework"}:
        return "Backend / Web"
    if topics & {"mobile", "android", "ios", "flutter", "react-native"}:
        return "Mobile"
    if topics & {"cli", "terminal", "command-line", "shell"}:
        return "CLI / Tools"
    if topics & {"education", "tutorial", "learning", "interview", "algorithm"}:
        return "Education / Docs"

    if any(w in desc for w in ["awesome", "curated list", "collection of"]):
        return "Awesome List"
    if any(w in desc for w in ["llm", "language model", "ai ", "machine learning", "deep learning", "neural"]):
        return "AI / ML"
    if any(w in desc for w in ["learn", "tutorial", "interview", "algorithm", "cookbook", "roadmap"]):
        return "Education / Docs"

    return "Other"


def generate_overview(metadata: dict[str, dict]) -> str:
    """Generate a markdown overview report from existing metadata."""
    lines = []
    lines.append("# Seed Repos Overview")
    lines.append("")
    lines.append(f"> Generated: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"> Total: {len(metadata)} repos")
    lines.append(f"> Source: existing metadata (no API calls)")
    lines.append("")

    # Summary stats
    has_wf = sum(1 for m in metadata.values() if m.get("workflow_count", 0) >= 2)
    low_wf = sum(1 for m in metadata.values() if m.get("workflow_count", 0) == 1)
    no_wf = sum(1 for m in metadata.values() if m.get("workflow_count", 0) == 0 and "error" not in m)
    archived = sum(1 for m in metadata.values() if m.get("archived"))
    no_lang = sum(1 for m in metadata.values() if not m.get("language") and "error" not in m)
    errors = sum(1 for m in metadata.values() if "error" in m)

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Workflows >= 2 | {has_wf} |")
    lines.append(f"| Workflows == 1 | {low_wf} |")
    lines.append(f"| No workflows | {no_wf} |")
    lines.append(f"| No language (likely docs/list) | {no_lang} |")
    lines.append(f"| Archived | {archived} |")
    lines.append(f"| Errors | {errors} |")
    lines.append("")

    # Category breakdown
    categories: dict[str, list[dict]] = {}
    for m in metadata.values():
        cat = "Error" if "error" in m else categorize(m)
        categories.setdefault(cat, []).append(m)

    lines.append("## By Category")
    lines.append("")
    lines.append("| Category | Count | WF >= 2 | No WF | Avg Stars |")
    lines.append("|----------|-------|---------|-------|-----------|")
    for cat in sorted(categories.keys()):
        repos = categories[cat]
        count = len(repos)
        good_wf = sum(1 for r in repos if r.get("workflow_count", 0) >= 2)
        bad_wf = sum(1 for r in repos if r.get("workflow_count", 0) == 0)
        avg_stars = sum(r.get("stars", 0) for r in repos) // max(count, 1)
        lines.append(f"| {cat} | {count} | {good_wf} | {bad_wf} | {avg_stars:,} |")
    lines.append("")

    # Language breakdown
    langs: dict[str, int] = {}
    for m in metadata.values():
        lang = m.get("language") or "(none)"
        langs[lang] = langs.get(lang, 0) + 1

    lines.append("## By Language")
    lines.append("")
    lines.append("| Language | Count |")
    lines.append("|----------|-------|")
    for lang, count in sorted(langs.items(), key=lambda x: -x[1])[:15]:
        lines.append(f"| {lang} | {count} |")
    lines.append("")

    # Detailed table per category
    lines.append("## Detailed List")
    lines.append("")

    for cat in sorted(categories.keys()):
        repos = sorted(categories[cat], key=lambda x: -x.get("stars", 0))
        lines.append(f"### {cat} ({len(repos)})")
        lines.append("")
        lines.append("| # | Repo | Stars | Lang | WF | Topics | Verdict |")
        lines.append("|---|------|-------|------|-----|--------|---------|")

        for i, m in enumerate(repos, 1):
            name = m.get("full_name", "?")
            stars = f"{m.get('stars', 0):,}"
            lang = m.get("language") or "-"
            wf = m.get("workflow_count", 0)
            wf_str = str(wf) if wf > 0 else "**0**"
            topics = ", ".join(m.get("topics", [])[:4]) or "-"

            # Verdict logic
            if "error" in m:
                verdict = "SKIP (error)"
            elif m.get("archived"):
                verdict = "SKIP (archived)"
            elif not m.get("language"):
                verdict = "SKIP (no lang)"
            elif wf == 0:
                verdict = "SKIP (no CI)"
            elif wf == 1:
                verdict = "SKIP (1 wf)"
            elif cat in ("Awesome List", "Education / Docs"):
                verdict = "SKIP (not code)"
            else:
                verdict = "OK"

            lines.append(f"| {i} | {name} | {stars} | {lang} | {wf_str} | {topics} | {verdict} |")

        lines.append("")

    # Summary
    ok = sum(
        1 for m in metadata.values()
        if m.get("workflow_count", 0) >= 2
        and not m.get("archived")
        and m.get("language")
        and "error" not in m
        and categorize(m) not in ("Awesome List", "Education / Docs")
    )
    skip = len(metadata) - ok

    lines.append("## Verdict Summary")
    lines.append("")
    lines.append(f"- **OK:** {ok} repos")
    lines.append(f"- **SKIP:** {skip} repos")
    lines.append("")

    return "\n".join(lines)


def main():
    meta_path = _find_latest_metadata()
    if not meta_path:
        logger.error("No metadata file found in %s", SEEDS_DIR)
        logger.error("Run build_seed_list.py first.")
        return

    logger.info("Reading metadata from %s", meta_path)
    metadata = json.loads(meta_path.read_text())
    logger.info("Loaded %d repos", len(metadata))

    # Generate overview
    overview = generate_overview(metadata)

    SEEDS_DIR.mkdir(parents=True, exist_ok=True)
    overview_file = SEEDS_DIR / f"overview-{RUN_TS}.md"
    overview_file.write_text(overview)
    logger.info("Saved overview to %s", overview_file)

    # Update symlink
    latest = SEEDS_DIR / "overview-latest.md"
    latest.unlink(missing_ok=True)
    latest.symlink_to(overview_file.name)

    print(f"\nDone! Open {overview_file}")


if __name__ == "__main__":
    main()
