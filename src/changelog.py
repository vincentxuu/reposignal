"""Workflow and pattern changelog generation."""

from __future__ import annotations

from typing import Any


def compute_workflow_changelog(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    """Compare two analysis snapshots and summarize workflow/pattern changes."""
    if not previous:
        return {"available": False, "added_workflows": [], "removed_workflows": [], "changed_patterns": []}

    current_workflows = _workflow_index(current)
    previous_workflows = _workflow_index(previous)
    added = sorted(set(current_workflows) - set(previous_workflows))
    removed = sorted(set(previous_workflows) - set(current_workflows))

    current_patterns = _repo_patterns(current)
    previous_patterns = _repo_patterns(previous)
    changed_patterns = []
    for repo in sorted(set(current_patterns) | set(previous_patterns)):
        added_patterns = sorted(current_patterns.get(repo, set()) - previous_patterns.get(repo, set()))
        removed_patterns = sorted(previous_patterns.get(repo, set()) - current_patterns.get(repo, set()))
        if added_patterns or removed_patterns:
            changed_patterns.append({
                "repo": repo,
                "added_patterns": added_patterns,
                "removed_patterns": removed_patterns,
            })

    return {
        "available": True,
        "added_workflows": [{"repo": repo, "workflow": workflow} for repo, workflow in added],
        "removed_workflows": [{"repo": repo, "workflow": workflow} for repo, workflow in removed],
        "changed_patterns": changed_patterns,
    }


def _workflow_index(results: dict[str, Any]) -> set[tuple[str, str]]:
    index = set()
    for repo in results.get("repo_summaries", []):
        for workflow in repo.get("workflows", []):
            index.add((repo["repo"], workflow.get("name", "")))
    return index


def _repo_patterns(results: dict[str, Any]) -> dict[str, set[str]]:
    return {
        repo["repo"]: set(repo.get("pattern_slugs", []))
        for repo in results.get("repo_summaries", [])
    }
