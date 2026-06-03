"""Lineage helpers that connect analysis outputs back to source workflow files."""

from __future__ import annotations

from typing import Any


def build_lineage(repo_summaries: list[dict[str, Any]], pattern_detection: dict[str, Any]) -> dict[str, Any]:
    """Build a compact source-file lineage map for analysis consumers."""
    workflows = []
    by_repo: dict[str, list[str]] = {}
    for repo in repo_summaries:
        repo_sources = []
        for workflow in repo.get("workflows", []):
            source_file = workflow.get("source_file") or workflow.get("path")
            item = {
                "repo": repo["repo"],
                "workflow": workflow.get("name", ""),
                "path": workflow.get("path", ""),
                "source_file": source_file,
            }
            workflows.append(item)
            if source_file:
                repo_sources.append(source_file)
        by_repo[repo["repo"]] = sorted(set(repo_sources))

    pattern_sources = {}
    for pattern in pattern_detection.get("patterns", []):
        sources = [
            {
                "repo": example.get("repo"),
                "workflow": example.get("workflow", ""),
                "path": example.get("path", ""),
                "source_file": example.get("source_file", ""),
            }
            for example in pattern.get("examples", [])
            if example.get("repo")
        ]
        pattern_sources[pattern["slug"]] = sources

    return {
        "workflow_sources": workflows,
        "sources_by_repo": by_repo,
        "pattern_sources": pattern_sources,
    }
