"""Crawl-free pipeline: reuse cached data/raw + cached enrichment, then
extract -> analyze -> report. Used when no valid GITHUB_TOKEN is available."""
import json
import logging
from pathlib import Path

from src.extractors.cicd import CICDExtractor
from src.analyzer import analyze
from src.reporter import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reanalyze")

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "data" / "cache"

# AI review actions from cache (union of all cached lists)
ai_cache = json.loads((CACHE / "ai_review_actions.json").read_text())
ai_review_actions = set()
for v in ai_cache.values():
    if isinstance(v, list):
        ai_review_actions.update(v)
logger.info("Loaded %d cached AI review actions", len(ai_review_actions))

# Action descriptions from cache
action_descs = json.loads((CACHE / "action_descriptions.json").read_text())
logger.info("Loaded %d cached action descriptions", len(action_descs))

# Extract from cached raw YAML
df = CICDExtractor(ai_review_actions=ai_review_actions).extract(raw_dir=ROOT / "data" / "raw")
logger.info("Extracted %d workflows", len(df))

# Analyze + report
results = analyze(action_descriptions=action_descs)
logger.info("Analysis complete: %d repos, %d workflows", results["total_repos"], results["total_workflows"])

report_path = generate_report(results)
logger.info("Report saved to %s", report_path)
