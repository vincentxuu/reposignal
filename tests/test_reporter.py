"""Tests for the reporter module."""
import pytest
from pathlib import Path

from src.reporter import generate_report


@pytest.fixture
def sample_results():
    """Return a sample results dict for testing."""
    return {
        "generated_at": "2026-03-29T00:00:00+00:00",
        "total_repos": 10,
        "total_workflows": 50,
        "matrix_usage": {"total_repos": 10, "matrix_repos": 7, "percentage": 70.0},
        "popular_actions": [{"action": "actions/checkout", "count": 45}],
        "popular_actions_categorized": [
            {"action": "actions/checkout", "count": 45, "category": "CI/Build",
             "desc": "Check out repository code", "desc_zh": "Checkout 程式碼", "url": "https://github.com/actions/checkout"},
        ],
        "ai_review_adoption": {
            "count": 2,
            "repos": ["owner/repo1", "owner/repo2"],
            "repos_detailed": [
                {"repo": "owner/repo1", "actions": ["anthropics/claude-code-action"], "url": "https://github.com/owner/repo1"},
                {"repo": "owner/repo2", "actions": ["anthropics/claude-code-action"], "url": "https://github.com/owner/repo2"},
            ],
            "tool_breakdown": [
                {"action": "anthropics/claude-code-action", "count": 2, "url": "https://github.com/anthropics/claude-code-action",
                 "name": "Claude Code Action", "model": "Claude (Anthropic)",
                 "approach": "Full codebase-aware review", "prompt_style": "Configurable"},
            ],
        },
        "security_scan_adoption": {"count": 1, "repos": ["owner/repo1"]},
        "permissions_usage": {
            "total_workflows": 50,
            "with_permissions": 30,
            "percentage": 60.0,
        },
        "workflow_fingerprints": [
            {
                "fingerprint": "abc123",
                "actions": ["actions/checkout"],
                "count": 20,
                "example_repos": ["owner/repo1"],
            }
        ],
        "insights": [],
        "recommendations": [],
        "diffs": [],
    }


@pytest.fixture(autouse=True)
def _patch_reports_dir(monkeypatch, tmp_path):
    """Redirect REPORTS_DIR to a temporary directory for every test."""
    monkeypatch.setattr("src.reporter.REPORTS_DIR", tmp_path)


class TestGenerateReportNoDiffs:
    """First run (no diffs) -- empty diffs list."""

    def test_report_file_is_created(self, tmp_path, sample_results):
        path = generate_report(sample_results, date="2026-03-29")
        assert path.exists()

    def test_report_does_not_contain_changes_section(self, tmp_path, sample_results):
        path = generate_report(sample_results, date="2026-03-29")
        content = path.read_text()
        assert "Changes Since Last Run" not in content


class TestGenerateReportWithDiffs:
    """With diffs -- verify the Changes Since Last Run table."""

    def test_report_contains_changes_table(self, tmp_path, sample_results):
        sample_results["diffs"] = [
            {
                "metric": "total_repos",
                "prev_value": 8,
                "curr_value": 10,
                "delta": 2,
            },
            {
                "metric": "total_workflows",
                "prev_value": 40,
                "curr_value": 50,
                "delta": 10,
            },
        ]
        path = generate_report(sample_results, date="2026-03-29")
        content = path.read_text()

        assert "Changes Since Last Run" in content
        assert "total_repos" in content
        assert "total_workflows" in content
        # Verify the delta values appear with the +sign format
        assert "+2" in content
        assert "+10" in content


class TestReportContainsAllSections:
    """Verify the generated report has all expected sections."""

    def test_all_sections_present(self, tmp_path, sample_results):
        path = generate_report(sample_results, date="2026-03-29")
        content = path.read_text()

        # 5 analysis sections
        assert "## 1. Matrix Strategy Usage" in content
        assert "## 2. Top" in content and "GitHub Actions" in content
        assert "## 3. AI-Based Code Review Adoption" in content
        assert "## 4. Security Posture" in content
        assert "## 5. Workflow Fingerprints" in content

        # Metadata
        assert "## Metadata" in content


class TestCustomDateParameter:
    """Custom date parameter -- verify filename uses the provided date."""

    def test_filename_uses_custom_date(self, tmp_path, sample_results):
        path = generate_report(sample_results, date="2026-01-01")
        assert path.name.startswith("patterns-2026-01-01-")
        assert path.name.endswith(".md")
        assert "zh-tw" not in path.name

    def test_date_appears_in_report_content(self, tmp_path, sample_results):
        path = generate_report(sample_results, date="2026-01-01")
        content = path.read_text()
        assert "2026-01-01" in content
