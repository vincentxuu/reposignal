"""Per-repo workflow summary construction."""

from typing import Any

import duckdb


COMMON_ACTIONS = {
    "actions/checkout", "actions/setup-python", "actions/setup-node",
    "actions/setup-go", "actions/setup-java", "actions/setup-dotnet",
    "actions/upload-artifact", "actions/download-artifact",
    "actions/cache", "actions/cache/restore", "actions/cache/save",
    "actions/github-script",
}

ALL_PRACTICES = [
    ("has_matrix", "Matrix testing", "Matrix 測試"),
    ("has_permissions", "Explicit permissions", "明確的 permissions"),
    ("has_security_scan", "Security scanning", "安全掃描"),
    ("has_ai_review", "AI code review", "AI 程式碼審查"),
    ("has_cache", "CI caching", "CI 快取"),
    ("has_concurrency", "Concurrency control", "並行控制"),
]


def build_repo_summaries(con: duckdb.DuckDBPyConnection, columns: list[str]) -> list[dict[str, Any]]:
    """Build per-repo diagnostic summaries from the `cicd` DuckDB view."""

    def col(name: str, default: str) -> str:
        return name if name in columns else f"{default} AS {name}"

    wf_rows = con.execute(f"""
        SELECT
            repo,
            workflow_name,
            {col("workflow_path", "workflow_name")},
            {col("source_file", "workflow_name")},
            triggers,
            job_names,
            uses_matrix,
            {col("matrix_keys", "[]")},
            {col("matrix_values", "[]")},
            uses_reusable_workflows,
            {col("reusable_workflows", "[]")},
            actions_normalized,
            has_permissions_block,
            runs_on,
            concurrency_set,
            has_ai_review,
            has_security_scan,
            {col("step_names", "[]")},
            {col("run_commands", "[]")}
        FROM cicd
        ORDER BY repo, workflow_name
    """).fetchall()

    repo_map: dict[str, dict[str, Any]] = {}
    for row in wf_rows:
        (repo, wf_name, workflow_path, source_file, triggers, job_names, uses_matrix,
         matrix_keys, matrix_values, uses_reusable, reusable_workflows,
         actions_norm, has_perms, runs_on, concurrency, has_ai, has_sec,
         step_names, run_commands) = row

        if repo not in repo_map:
            repo_map[repo] = {
                "repo": repo,
                "url": f"https://github.com/{repo}",
                "workflows": [],
                "all_actions": set(),
                "has_matrix": False,
                "has_permissions": False,
                "has_ai_review": False,
                "has_security_scan": False,
                "has_cache": False,
                "has_concurrency": False,
                "has_reusable_workflows": False,
            }

        entry = repo_map[repo]
        actions_list = [a for a in (actions_norm or []) if a]
        notable = [a for a in actions_list if a not in COMMON_ACTIONS and not a.startswith(".")]

        entry["workflows"].append({
            "name": wf_name,
            "path": workflow_path,
            "source_file": source_file,
            "triggers": list(triggers) if triggers else [],
            "jobs": list(job_names) if job_names else [],
            "job_count": len(job_names) if job_names else 0,
            "actions": actions_list,
            "notable_actions": notable,
            "uses_matrix": uses_matrix,
            "matrix_keys": list(matrix_keys) if matrix_keys else [],
            "matrix_values": list(matrix_values) if matrix_values else [],
            "has_permissions": has_perms,
            "has_ai_review": has_ai,
            "has_security_scan": has_sec,
            "runs_on": list(runs_on) if runs_on else [],
            "has_concurrency": concurrency,
            "uses_reusable_workflows": uses_reusable,
            "reusable_workflows": list(reusable_workflows) if reusable_workflows else [],
            "step_names": list(step_names) if step_names else [],
            "run_commands": list(run_commands) if run_commands else [],
        })
        entry["all_actions"].update(actions_list)
        entry["has_matrix"] = entry["has_matrix"] or bool(uses_matrix)
        entry["has_permissions"] = entry["has_permissions"] or bool(has_perms)
        entry["has_ai_review"] = entry["has_ai_review"] or bool(has_ai)
        entry["has_security_scan"] = entry["has_security_scan"] or bool(has_sec)
        entry["has_concurrency"] = entry["has_concurrency"] or bool(concurrency)
        entry["has_reusable_workflows"] = entry["has_reusable_workflows"] or bool(uses_reusable)
        entry["has_cache"] = entry["has_cache"] or any("cache" in a.lower() for a in actions_list)

    summaries = []
    for repo in sorted(repo_map):
        entry = repo_map[repo]
        score = sum(1 for key, _, _ in ALL_PRACTICES if entry.get(key))
        max_score = len(ALL_PRACTICES)
        summaries.append({
            "repo": entry["repo"],
            "url": entry["url"],
            "workflow_count": len(entry["workflows"]),
            "workflows": entry["workflows"],
            "action_count": len(entry["all_actions"]),
            "notable_actions": sorted({a for wf in entry["workflows"] for a in wf["notable_actions"]}),
            "maturity_score": score,
            "maturity_max": max_score,
            "maturity_pct": round(score / max_score * 100) if max_score else 0,
            "missing_en": [en for key, en, _ in ALL_PRACTICES if not entry.get(key)],
            "missing_zh": [zh for key, _, zh in ALL_PRACTICES if not entry.get(key)],
            "has_matrix": entry["has_matrix"],
            "has_permissions": entry["has_permissions"],
            "has_ai_review": entry["has_ai_review"],
            "has_security_scan": entry["has_security_scan"],
            "has_cache": entry["has_cache"],
            "has_concurrency": entry["has_concurrency"],
            "has_reusable_workflows": entry["has_reusable_workflows"],
        })

    return sorted(summaries, key=lambda r: (-r["maturity_score"], r["repo"]))
