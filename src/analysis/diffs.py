"""Metric diff helpers for analysis snapshots."""

from typing import Any


def compute_diffs(
    current: dict[str, Any], previous: dict[str, Any]
) -> list[dict[str, Any]]:
    """Compute scalar metric diffs between current and previous analysis runs."""
    diffs: list[dict[str, Any]] = []
    metric_paths = [
        ("matrix_usage_percentage", "matrix_usage", "percentage"),
        ("permissions_usage_percentage", "permissions_usage", "percentage"),
        ("ai_review_count", "ai_review_adoption", "count"),
        ("total_repos", None, None),
        ("total_workflows", None, None),
    ]

    for metric_name, section, key in metric_paths:
        if section and key:
            prev_val = previous.get(section, {}).get(key, 0)
            curr_val = current.get(section, {}).get(key, 0)
        else:
            prev_val = previous.get(metric_name, 0)
            curr_val = current.get(metric_name, 0)

        if prev_val != curr_val:
            diffs.append({
                "metric": metric_name,
                "prev_value": prev_val,
                "curr_value": curr_val,
                "delta": curr_val - prev_val,
            })

    return diffs
