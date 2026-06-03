"""RepoSignal — Pipeline Entrypoint."""

import asyncio
import logging
import sys
from pathlib import Path

from src.crawler import crawl
from src.enricher import discover_ai_review_actions, fetch_action_descriptions
from src.extractors.cicd import CICDExtractor
from src.extended_crawler import (
    crawl_extended_batch1,
    crawl_extended_batch2,
    crawl_extended_batch3,
)
from src.analyzer import analyze
from src.reporter import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent


async def main():
    seed_file = PROJECT_ROOT / "seed_repos.json"
    if not seed_file.exists():
        logger.error(
            "seed_repos.json not found. Run: python src/scripts/build_seed_list.py"
        )
        sys.exit(1)

    # Step 1: Crawl
    logger.info("=== Step 1: Crawling workflow files ===")
    stats = await crawl(seed_file)
    logger.info(
        "Crawl complete: %d repos, %d files, %d errors",
        stats["repos_crawled"],
        stats["files_downloaded"],
        stats["errors"],
    )

    # Step 1b: Extended repo observations (Batch 1)
    logger.info("=== Step 1b: Crawling extended Batch 1 repo signals ===")
    extended = await crawl_extended_batch1(seed_file)
    logger.info(
        "Extended crawl complete: %d repos, %d requests, %d errors",
        extended["stats"]["repos_observed"],
        extended["stats"]["requests"],
        extended["stats"]["errors"],
    )

    logger.info("=== Step 1c: Crawling extended Batch 2 config trends ===")
    config_trends = await crawl_extended_batch2(seed_file)
    logger.info(
        "Config trend crawl complete: %d repos, %d files, %d parse errors",
        config_trends["stats"]["repos_observed"],
        config_trends["stats"]["files_found"],
        config_trends["stats"]["parse_errors"],
    )

    logger.info("=== Step 1d: Crawling extended Batch 3 structural signals ===")
    structures = await crawl_extended_batch3(seed_file)
    logger.info(
        "Structural signal crawl complete: %d repos, %d requests, %d errors",
        structures["stats"]["repos_observed"],
        structures["stats"]["requests"],
        structures["stats"]["errors"],
    )

    # Step 2: Discover AI review actions
    logger.info("=== Step 2: Discovering AI review actions ===")
    ai_review_actions = await discover_ai_review_actions()
    logger.info("Found %d AI review actions", len(ai_review_actions))

    # Step 3: Extract
    logger.info("=== Step 3: Extracting workflow data ===")
    extractor = CICDExtractor(ai_review_actions=ai_review_actions)
    df = extractor.extract(raw_dir=PROJECT_ROOT / "data" / "raw")
    logger.info("Extracted %d workflows", len(df))

    # Step 4: Enrich action descriptions
    logger.info("=== Step 4: Fetching action.yml descriptions ===")
    import polars as pl
    actions_col = df["actions_normalized"].explode().drop_nulls().unique().to_list()
    action_descs = await fetch_action_descriptions(actions_col)
    logger.info("Enriched %d action descriptions", sum(1 for v in action_descs.values() if v))

    # Step 5: Analyze
    logger.info("=== Step 5: Analyzing patterns ===")
    results = analyze(action_descriptions=action_descs)
    logger.info("Analysis complete: %d repos, %d workflows", results["total_repos"], results["total_workflows"])

    # Step 6: Report
    logger.info("=== Step 6: Generating report ===")
    report_path = generate_report(results)
    logger.info("Report saved to %s", report_path)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    asyncio.run(main())
