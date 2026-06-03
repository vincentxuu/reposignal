"""Tests for pattern detection, security scoring, and data quality checks."""

import polars as pl

from src.patterns import detect_patterns
from src.quality import summarize_quality
from src.security import score_security_posture


def test_detects_research_patterns_from_repo_summary() -> None:
    repos = [
        {
            "repo": "example/project",
            "url": "https://github.com/example/project",
            "workflow_count": 1,
            "workflows": [
                {
                    "name": "ai-security-release",
                    "triggers": ["pull_request"],
                    "jobs": ["review"],
                    "actions": [
                        "actions/checkout",
                        "anthropics/claude-code-action",
                        "aquasecurity/trivy-action",
                        "sigstore/cosign-installer",
                        "step-security/harden-runner",
                        "pkg-pr-new/pkg-pr-new",
                    ],
                    "notable_actions": [],
                    "runs_on": ["ubuntu-latest"],
                    "uses_matrix": True,
                    "matrix_keys": ["python-version"],
                    "matrix_values": ["3.11", "3.12", "3.14"],
                    "has_permissions": True,
                    "has_ai_review": True,
                    "has_security_scan": True,
                    "uses_reusable_workflows": False,
                    "step_names": ["security audit"],
                    "run_commands": ["python -m pytest --benchmark"],
                }
            ],
        }
    ]

    result = detect_patterns(repos)
    slugs = {pattern["slug"] for pattern in result["patterns"] if pattern["repo_count"]}

    assert "ai-code-review" in slugs
    assert "ai-security-review" in slugs
    assert "security-scanning" in slugs
    assert "container-signing" in slugs
    assert "harden-runner" in slugs
    assert "cross-version-compat" in slugs
    assert "performance-tracking" in slugs


def test_detects_tier3_release_train_with_workflow_dependencies() -> None:
    repos = [
        {
            "repo": "example/release-train",
            "url": "https://github.com/example/release-train",
            "workflow_count": 2,
            "workflows": [
                {
                    "name": "release-start",
                    "triggers": ["workflow_dispatch"],
                    "jobs": ["start"],
                    "actions": ["actions/checkout"],
                    "notable_actions": [],
                    "runs_on": ["ubuntu-latest"],
                    "uses_matrix": False,
                    "matrix_keys": [],
                    "matrix_values": [],
                    "has_permissions": True,
                    "has_ai_review": False,
                    "has_security_scan": False,
                    "uses_reusable_workflows": False,
                    "step_names": ["start release"],
                    "run_commands": ["gh workflow run release-promote.yml"],
                    "path": ".github/workflows/release-start.yml",
                    "source_file": "data/raw/example/release-train/release-start.yml",
                },
                {
                    "name": "release-promote",
                    "triggers": ["workflow_run"],
                    "jobs": ["promote"],
                    "actions": ["actions/checkout"],
                    "notable_actions": [],
                    "runs_on": ["ubuntu-latest"],
                    "uses_matrix": False,
                    "matrix_keys": [],
                    "matrix_values": [],
                    "has_permissions": True,
                    "has_ai_review": False,
                    "has_security_scan": False,
                    "uses_reusable_workflows": False,
                    "step_names": ["promote release"],
                    "run_commands": [],
                    "path": ".github/workflows/release-promote.yml",
                    "source_file": "data/raw/example/release-train/release-promote.yml",
                },
            ],
        }
    ]

    result = detect_patterns(repos)
    release = next(pattern for pattern in result["patterns"] if pattern["slug"] == "multi-stage-release")

    assert release["repo_count"] == 1


def test_security_score_uses_weighted_dimensions() -> None:
    repos = [
        {
            "repo": "example/secure",
            "url": "https://github.com/example/secure",
            "workflows": [
                {
                    "name": "secure",
                    "actions": [
                        "github/codeql-action/init",
                        "aquasecurity/trivy-action",
                        "gitleaks/gitleaks-action",
                        "ossf/scorecard-action",
                        "sigstore/cosign-installer",
                        "step-security/harden-runner",
                        "actions/create-github-app-token",
                    ],
                    "run_commands": ["syft packages dir:. --output sbom.spdx"],
                    "step_names": [],
                    "has_permissions": True,
                }
            ],
        }
    ]

    result = score_security_posture(repos)

    assert result["scores"][0]["score"] > 80
    assert result["scores"][0]["dimensions"]["permissions"] == 25
    assert "github/codeql-action/init" in result["scores"][0]["security_tools"]


def test_quality_summary_flags_missing_columns_and_duplicates() -> None:
    df = pl.DataFrame(
        {
            "repo": ["a/b", "a/b"],
            "workflow_name": ["ci", "ci"],
            "workflow_path": [".github/workflows/ci.yml", ".github/workflows/ci.yml"],
            "crawl_date": ["2026-03-29", "2026-03-29"],
            "triggers": [["push"], ["push"]],
            "job_names": [["test"], ["test"]],
            "uses_matrix": [False, False],
            "actions_normalized": [["actions/checkout"], ["actions/checkout"]],
            "has_permissions_block": [True, True],
        }
    )

    result = summarize_quality(df)

    assert result["status"] in {"warn", "fail"}
    assert result["duplicate_count"] == 1
    assert "has_security_scan" in result["missing_columns"]
