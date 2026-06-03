"""Analyzer orchestration for RepoSignal.

Reads processed Parquet data via DuckDB and assembles a structured analysis
payload for reports, repo profiles, and future site/API consumers.
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from src.analysis.actions import AI_REVIEW_TOOLS, categorize_actions
from src.analysis.diffs import compute_diffs as _compute_diffs
from src.analysis.intelligence import generate_insights, generate_recommendations
from src.analysis.repo_summary import build_repo_summaries
from src.changelog import compute_workflow_changelog
from src.lineage import build_lineage
from src.patterns import detect_patterns
from src.profiles import generate_profiles
from src.quality import summarize_quality
from src.security import score_security_posture

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PARQUET_PATH = DATA_DIR / "processed" / "cicd.parquet"
ANALYSIS_DIR = DATA_DIR / "analysis"
CURRENT_JSON = ANALYSIS_DIR / "current.json"
PREVIOUS_JSON = ANALYSIS_DIR / "previous.json"


def _empty_results() -> dict[str, Any]:
    """Return an empty results skeleton when no data is available."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repos": 0,
        "total_workflows": 0,
        "matrix_usage": {"total_repos": 0, "matrix_repos": 0, "percentage": 0.0},
        "popular_actions": [],
        "ai_review_adoption": {"count": 0, "repos": []},
        "permissions_usage": {
            "total_workflows": 0,
            "with_permissions": 0,
            "percentage": 0.0,
        },
        "workflow_fingerprints": [],
        "pattern_detection": {"total_patterns": 21, "detected_patterns": 0, "patterns": [], "categories": []},
        "security_posture": {"average_score": 0.0, "top": [], "bottom": [], "scores": []},
        "workflow_changelog": {"available": False, "added_workflows": [], "removed_workflows": [], "changed_patterns": []},
        "data_quality": {"status": "pass", "row_count": 0, "repo_count": 0, "missing_columns": [], "duplicate_count": 0, "null_rates": {}, "issues": []},
        "lineage": {"workflow_sources": [], "sources_by_repo": {}, "pattern_sources": {}},
        "profiles": [],
        "diffs": [],
    }


def _md5_fingerprint(actions: list[str]) -> str:
    """Compute MD5 of sorted, comma-joined action names."""
    return hashlib.md5(",".join(sorted(actions)).encode()).hexdigest()


def _load_previous_results() -> dict[str, Any] | None:
    if not PREVIOUS_JSON.exists():
        return None
    try:
        return json.loads(PREVIOUS_JSON.read_text())
    except json.JSONDecodeError as exc:
        logger.warning("Could not load previous results: %s", exc)
        return None


def _available_columns(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [col[0] for col in con.execute("DESCRIBE cicd").fetchall()]


def _matrix_usage(con: duckdb.DuckDBPyConnection, columns: list[str], total_repos: int) -> dict[str, Any]:
    if "uses_matrix" not in columns:
        logger.warning("Column 'uses_matrix' not found; skipping matrix_usage query")
        return {"total_repos": total_repos, "matrix_repos": 0, "percentage": 0.0}
    matrix_total, matrix_count = con.execute("""
        SELECT
            count(DISTINCT repo) AS total,
            count(DISTINCT CASE WHEN uses_matrix THEN repo END) AS matrix
        FROM cicd
    """).fetchone()
    percentage = round(matrix_count / matrix_total * 100, 2) if matrix_total else 0.0
    return {"total_repos": matrix_total, "matrix_repos": matrix_count, "percentage": percentage}


def _popular_actions(con: duckdb.DuckDBPyConnection, columns: list[str]) -> list[dict[str, Any]]:
    if "actions_normalized" not in columns:
        logger.warning("No actions_normalized column found; skipping popular_actions query")
        return []
    rows = con.execute("""
        SELECT action_name, count(*) AS usage_count
        FROM (
            SELECT unnest(actions_normalized) AS action_name
            FROM cicd
            WHERE actions_normalized IS NOT NULL
        )
        WHERE action_name IS NOT NULL AND action_name != ''
        GROUP BY action_name
        ORDER BY usage_count DESC
        LIMIT 50
    """).fetchall()
    return [{"action": row[0].strip(), "count": row[1]} for row in rows]


def _ai_review_adoption(con: duckdb.DuckDBPyConnection, columns: list[str]) -> dict[str, Any]:
    if "has_ai_review" in columns and "ai_review_actions" in columns:
        ai_rows = con.execute("""
            SELECT repo, ai_review_actions
            FROM cicd
            WHERE has_ai_review = true
            ORDER BY repo
        """).fetchall()
        ai_repo_map: dict[str, list[str]] = {}
        for repo, actions in ai_rows:
            ai_repo_map.setdefault(repo, [])
            for action in actions or []:
                if action and action not in ai_repo_map[repo]:
                    ai_repo_map[repo].append(action)
        repos_detailed = [
            {"repo": repo, "actions": actions, "url": f"https://github.com/{repo}"}
            for repo, actions in sorted(ai_repo_map.items())
        ]
        tool_counts: dict[str, int] = {}
        for entry in repos_detailed:
            for action in entry["actions"]:
                tool_counts[action] = tool_counts.get(action, 0) + 1
        tool_breakdown = [
            {
                "action": action,
                "count": count,
                "url": f"https://github.com/{action}",
                **(AI_REVIEW_TOOLS.get(action, {})),
            }
            for action, count in sorted(tool_counts.items(), key=lambda item: -item[1])
        ]
    elif "has_ai_review" in columns:
        rows = con.execute("""
            SELECT DISTINCT repo
            FROM cicd
            WHERE has_ai_review = true
            ORDER BY repo
        """).fetchall()
        repos_detailed = [
            {"repo": row[0], "actions": [], "url": f"https://github.com/{row[0]}"}
            for row in rows
        ]
        tool_breakdown = []
    else:
        logger.warning("Column 'has_ai_review' not found; skipping ai_review_adoption query")
        repos_detailed = []
        tool_breakdown = []

    return {
        "count": len(repos_detailed),
        "repos": [entry["repo"] for entry in repos_detailed],
        "repos_detailed": repos_detailed,
        "tool_breakdown": tool_breakdown,
    }


def _permissions_usage(
    con: duckdb.DuckDBPyConnection, columns: list[str], total_workflows: int
) -> dict[str, Any]:
    if "has_permissions_block" not in columns:
        logger.warning("Column 'has_permissions_block' not found; skipping permissions_usage query")
        return {"total_workflows": total_workflows, "with_permissions": 0, "percentage": 0.0}
    total, with_permissions = con.execute("""
        SELECT
            count(*) AS total,
            count(CASE WHEN has_permissions_block THEN 1 END) AS with_perm
        FROM cicd
    """).fetchone()
    percentage = round(with_permissions / total * 100, 2) if total else 0.0
    return {"total_workflows": total, "with_permissions": with_permissions, "percentage": percentage}


def _workflow_fingerprints(con: duckdb.DuckDBPyConnection, columns: list[str]) -> list[dict[str, Any]]:
    if "actions_normalized" not in columns:
        logger.warning("No actions column found; skipping workflow_fingerprints query")
        return []
    rows = con.execute("""
        SELECT list_sort(actions_normalized) AS sorted_actions, repo
        FROM cicd
        WHERE actions_normalized IS NOT NULL AND len(actions_normalized) > 0
    """).fetchall()
    groups: dict[str, dict[str, Any]] = {}
    for actions_list, repo in rows:
        parts = [a for a in actions_list if a] if actions_list else []
        fingerprint = _md5_fingerprint(parts)
        groups.setdefault(fingerprint, {
            "fingerprint": fingerprint,
            "actions": sorted(parts),
            "count": 0,
            "example_repos": [],
        })
        groups[fingerprint]["count"] += 1
        if len(groups[fingerprint]["example_repos"]) < 3 and repo not in groups[fingerprint]["example_repos"]:
            groups[fingerprint]["example_repos"].append(repo)
    return sorted(groups.values(), key=lambda item: item["count"], reverse=True)[:10]


def _security_scan_adoption(con: duckdb.DuckDBPyConnection, columns: list[str]) -> dict[str, Any]:
    if "has_security_scan" not in columns:
        return {"count": 0, "repos": []}
    rows = con.execute("""
        SELECT DISTINCT repo
        FROM cicd
        WHERE has_security_scan = true
        ORDER BY repo
    """).fetchall()
    repos = [row[0] for row in rows]
    return {"count": len(repos), "repos": repos}


def analyze(
    action_descriptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run all analysis queries and return a structured results dict."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    if not PARQUET_PATH.exists():
        logger.warning("Parquet file not found at %s; returning empty results", PARQUET_PATH)
        results = _empty_results()
        _persist(results)
        return results

    con = duckdb.connect(database=":memory:")
    con.execute(f"CREATE VIEW cicd AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
    row_count = con.execute("SELECT count(*) FROM cicd").fetchone()[0]
    if row_count == 0:
        logger.warning("Parquet file has 0 rows; returning empty results")
        con.close()
        results = _empty_results()
        _persist(results)
        return results

    logger.info("Analyzing %d rows from %s", row_count, PARQUET_PATH)
    columns = _available_columns(con)
    data_quality = summarize_quality(pl.read_parquet(PARQUET_PATH))
    total_repos = con.execute("SELECT count(DISTINCT repo) FROM cicd").fetchone()[0]
    total_workflows = row_count
    previous_results = _load_previous_results()

    popular_actions = _popular_actions(con, columns)
    repo_summaries = build_repo_summaries(con, columns)
    pattern_detection = detect_patterns(repo_summaries)
    security_posture = score_security_posture(repo_summaries)
    lineage = build_lineage(repo_summaries, pattern_detection)

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_repos": total_repos,
        "total_workflows": total_workflows,
        "matrix_usage": _matrix_usage(con, columns, total_repos),
        "popular_actions": popular_actions,
        "popular_actions_categorized": categorize_actions(popular_actions, action_descriptions),
        "ai_review_adoption": _ai_review_adoption(con, columns),
        "security_scan_adoption": _security_scan_adoption(con, columns),
        "permissions_usage": _permissions_usage(con, columns, total_workflows),
        "workflow_fingerprints": _workflow_fingerprints(con, columns),
        "repo_summaries": repo_summaries,
        "pattern_detection": pattern_detection,
        "security_posture": security_posture,
        "workflow_changelog": {"available": False, "added_workflows": [], "removed_workflows": [], "changed_patterns": []},
        "data_quality": data_quality,
        "lineage": lineage,
        "profiles": [],
        "insights": [],
        "recommendations": [],
        "diffs": [],
    }
    con.close()

    results["insights"] = generate_insights(results)
    results["recommendations"] = generate_recommendations(results)
    results["workflow_changelog"] = compute_workflow_changelog(results, previous_results)

    try:
        results["profiles"] = generate_profiles(results)
    except Exception as exc:
        logger.warning("Could not generate repo profiles: %s", exc)

    if previous_results:
        results["diffs"] = _compute_diffs(results, previous_results)
        logger.info("Found %d metric diffs from previous run", len(results["diffs"]))

    _persist(results)
    return results


def _persist(results: dict[str, Any]) -> None:
    """Save current results and copy to previous.json for next run."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_JSON.write_text(json.dumps(results, indent=2, default=str))
    shutil.copy2(CURRENT_JSON, PREVIOUS_JSON)
    logger.info("Saved analysis to %s", CURRENT_JSON)
