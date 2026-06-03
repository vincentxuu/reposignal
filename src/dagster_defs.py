"""Dagster asset definitions for the RepoSignal pipeline."""

import asyncio
from pathlib import Path

from dagster import AssetExecutionContext, Definitions, MetadataValue, asset

from src.analyzer import analyze
from src.crawler import RAW_DIR, SEED_FILE, crawl
from src.enricher import discover_ai_review_actions, fetch_action_descriptions
from src.extended_crawler import (
    BATCH1_OUTPUT,
    BATCH2_OUTPUT,
    BATCH3_OUTPUT,
    crawl_extended_batch1,
    crawl_extended_batch2,
    crawl_extended_batch3,
)
from src.extractors.cicd import CICDExtractor
from src.reporter import generate_report
from src.validation import validate_cicd_dataframe


@asset
def raw_workflows(context: AssetExecutionContext) -> dict:
    """Extract raw GitHub Actions workflow YAML into `data/raw/`."""
    stats = asyncio.run(crawl(SEED_FILE))
    context.add_output_metadata({
        "repos_crawled": stats.get("repos_crawled", 0),
        "files_downloaded": stats.get("files_downloaded", 0),
        "errors": stats.get("errors", 0),
    })
    return stats


@asset(deps=[raw_workflows])
def extended_batch1(context: AssetExecutionContext) -> dict:
    """Extract Batch 1 beyond-CI file-presence signals into `data/configs/`."""
    result = asyncio.run(crawl_extended_batch1(SEED_FILE))
    context.add_output_metadata({
        "path": MetadataValue.path(str(BATCH1_OUTPUT)),
        "repos_observed": result["stats"]["repos_observed"],
        "requests": result["stats"]["requests"],
        "errors": result["stats"]["errors"],
    })
    return result


@asset(deps=[extended_batch1])
def extended_batch2(context: AssetExecutionContext) -> dict:
    """Extract Batch 2 parsed config trends into `data/configs/`."""
    result = asyncio.run(crawl_extended_batch2(SEED_FILE))
    context.add_output_metadata({
        "path": MetadataValue.path(str(BATCH2_OUTPUT)),
        "repos_observed": result["stats"]["repos_observed"],
        "files_found": result["stats"]["files_found"],
        "parse_errors": result["stats"]["parse_errors"],
    })
    return result


@asset(deps=[extended_batch2])
def extended_batch3(context: AssetExecutionContext) -> dict:
    """Extract Batch 3 structural signals into `data/configs/`."""
    result = asyncio.run(crawl_extended_batch3(SEED_FILE))
    context.add_output_metadata({
        "path": MetadataValue.path(str(BATCH3_OUTPUT)),
        "repos_observed": result["stats"]["repos_observed"],
        "requests": result["stats"]["requests"],
        "errors": result["stats"]["errors"],
    })
    return result


@asset(deps=[raw_workflows])
def cicd_parquet(context: AssetExecutionContext) -> str:
    """Transform raw workflow YAML into validated latest and partitioned Parquet."""
    ai_review_actions = asyncio.run(discover_ai_review_actions())
    df = CICDExtractor(ai_review_actions=ai_review_actions).extract(raw_dir=RAW_DIR)
    quality = validate_cicd_dataframe(df)
    output = Path("data/processed/cicd.parquet")
    context.add_output_metadata({
        "path": MetadataValue.path(str(output)),
        "rows": quality["row_count"],
        "repos": quality["repo_count"],
        "quality_status": quality["status"],
    })
    return str(output)


@asset(deps=[cicd_parquet, extended_batch3])
def analysis_json(context: AssetExecutionContext) -> str:
    """Analyze validated Parquet and write `data/analysis/current.json`."""
    from polars import read_parquet

    actions_col = read_parquet("data/processed/cicd.parquet")["actions_normalized"].explode().drop_nulls().unique().to_list()
    action_descriptions = asyncio.run(fetch_action_descriptions(actions_col))
    results = analyze(action_descriptions=action_descriptions)
    output = Path("data/analysis/current.json")
    context.add_output_metadata({
        "path": MetadataValue.path(str(output)),
        "repos": results["total_repos"],
        "workflows": results["total_workflows"],
        "patterns_detected": results["pattern_detection"]["detected_patterns"],
    })
    return str(output)


@asset(deps=[analysis_json])
def report_markdown(context: AssetExecutionContext) -> str:
    """Render bilingual Markdown reports from the current analysis payload."""
    import json

    results = json.loads(Path("data/analysis/current.json").read_text(encoding="utf-8"))
    path = generate_report(results)
    context.add_output_metadata({"path": MetadataValue.path(str(path))})
    return str(path)


defs = Definitions(assets=[
    raw_workflows,
    extended_batch1,
    extended_batch2,
    extended_batch3,
    cicd_parquet,
    analysis_json,
    report_markdown,
])
