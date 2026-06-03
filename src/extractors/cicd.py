"""CI/CD workflow extractor — parses GitHub Actions YAML files into a Polars DataFrame."""

import logging
import json
import re
from datetime import date
from typing import Any
from pathlib import Path

import polars as pl
import yaml

from src.models import WorkflowRecord

logger = logging.getLogger(__name__)

SECURITY_SCAN_PATTERNS = re.compile(
    r"trivy|snyk|grype|codeql|semgrep|gitleaks|scorecard", re.IGNORECASE
)
# Fallback regex — used only when no dynamic AI review actions set is provided
AI_REVIEW_PATTERNS = re.compile(r"claude|copilot|ai-review", re.IGNORECASE)

DATA_DIR = Path("data")


class CICDExtractor:
    name: str = "cicd"
    file_glob: str = ".github/workflows/*.yml"

    def __init__(self, ai_review_actions: set[str] | None = None):
        """Initialize extractor.

        Args:
            ai_review_actions: Set of known AI review action names (normalized,
                e.g. "anthropics/claude-code-action"). If provided, uses exact
                matching instead of regex for AI review detection.
        """
        self._ai_review_actions = ai_review_actions

    def extract(self, raw_dir: Path, *, crawl_date: date | None = None) -> pl.DataFrame:
        """Walk data/raw/{owner}/{repo}/ and parse all workflow YAML files."""
        crawl_date = crawl_date or date.today()
        error_log = DATA_DIR / "errors" / f"{crawl_date.isoformat()}.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)

        rows: list[dict] = []

        for owner_dir in sorted(raw_dir.iterdir()):
            if not owner_dir.is_dir():
                continue
            for repo_dir in sorted(owner_dir.iterdir()):
                if not repo_dir.is_dir():
                    continue
                for yml_path in sorted(
                    [*repo_dir.glob("*.yml"), *repo_dir.glob("*.yaml")]
                ):
                    row = self._parse_workflow(
                        yml_path,
                        owner=owner_dir.name,
                        repo=repo_dir.name,
                        error_log=error_log,
                        crawl_date=crawl_date,
                    )
                    if row is not None:
                        rows.append(row)

        df = pl.DataFrame(rows) if rows else self._empty_dataframe()

        out_path = DATA_DIR / "processed" / "cicd.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(out_path)
        logger.info("Wrote %d rows to %s", len(df), out_path)

        partition_path = DATA_DIR / "processed" / f"crawl_date={crawl_date.isoformat()}" / "cicd.parquet"
        partition_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(partition_path)
        logger.info("Wrote partitioned snapshot to %s", partition_path)

        return df

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_workflow(
        self,
        path: Path,
        *,
        owner: str,
        repo: str,
        error_log: Path,
        crawl_date: date,
    ) -> dict | None:
        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        except Exception as exc:
            msg = f"[{owner}/{repo}] Failed to parse {path}: {exc}"
            logger.warning(msg)
            with error_log.open("a") as f:
                f.write(msg + "\n")
            return None

        if not isinstance(data, dict):
            msg = f"[{owner}/{repo}] Skipping {path}: top-level is not a mapping"
            logger.warning(msg)
            with error_log.open("a") as f:
                f.write(msg + "\n")
            return None

        triggers = self._extract_triggers(data)
        jobs: dict = data.get("jobs") or {}

        actions_used = self._collect_actions(jobs)
        actions_normalized = [a.split("@")[0] for a in actions_used]
        runs_on = self._collect_runs_on(jobs)
        matrix_keys, matrix_values = self._collect_matrix(jobs)
        reusable_workflows = self._collect_reusable_workflows(jobs)
        step_names, run_commands = self._collect_steps(jobs)
        ai_review_actions = self._detect_ai_review(actions_normalized)

        record = WorkflowRecord(
            repo=f"{owner}/{repo}",
            workflow_name=path.stem,
            workflow_path=f".github/workflows/{path.name}",
            source_file=str(path),
            crawl_date=crawl_date,
            triggers=triggers,
            job_names=list(jobs.keys()),
            uses_matrix=any(
                isinstance(j, dict)
                and isinstance(j.get("strategy"), dict)
                and "matrix" in j["strategy"]
                for j in jobs.values()
            ),
            matrix_keys=matrix_keys,
            matrix_values=matrix_values,
            uses_reusable_workflows=len(reusable_workflows) > 0,
            reusable_workflows=reusable_workflows,
            actions_used=actions_used,
            actions_normalized=actions_normalized,
            has_permissions_block="permissions" in data,
            permissions=self._serialize_permissions(data.get("permissions")),
            runs_on=runs_on,
            concurrency_set="concurrency" in data,
            ai_review_actions=ai_review_actions,
            has_ai_review=len(ai_review_actions) > 0,
            has_security_scan=any(
                SECURITY_SCAN_PATTERNS.search(a) for a in actions_used
            ),
            step_names=step_names,
            run_commands=run_commands,
        )
        return record.model_dump(mode="json")

    @staticmethod
    def _extract_triggers(data: dict) -> list[str]:
        """Extract trigger event names from the `on:` field.

        PyYAML parses bare `on:` as the boolean True, so we handle that case
        by falling back to re-scanning the raw keys.
        """
        # `on` is a reserved word in YAML 1.1 — safe_load turns the key into True
        raw = data.get(True) or data.get("on")
        if raw is None:
            return []
        if isinstance(raw, bool):
            # Could not resolve the triggers; the key was literally `True`
            return []
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            return [str(item) for item in raw]
        if isinstance(raw, dict):
            return list(raw.keys())
        return []

    def _detect_ai_review(self, actions_normalized: list[str]) -> list[str]:
        """Detect AI review actions using dynamic set or fallback regex."""
        if self._ai_review_actions:
            return [a for a in actions_normalized if a in self._ai_review_actions]
        return [a for a in actions_normalized if AI_REVIEW_PATTERNS.search(a)]

    @staticmethod
    def _collect_actions(jobs: dict) -> list[str]:
        actions: list[str] = []
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                uses = step.get("uses")
                if isinstance(uses, str):
                    actions.append(uses)
        return actions

    @staticmethod
    def _collect_runs_on(jobs: dict) -> list[str]:
        result: list[str] = []
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            runs_on = job.get("runs-on")
            if isinstance(runs_on, str):
                result.append(runs_on)
            elif isinstance(runs_on, list):
                result.extend(str(r) for r in runs_on)
        return result

    @staticmethod
    def _serialize_permissions(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, sort_keys=True)

    @staticmethod
    def _collect_reusable_workflows(jobs: dict) -> list[str]:
        workflows: list[str] = []
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            uses = job.get("uses")
            if isinstance(uses, str):
                workflows.append(uses)
        return workflows

    @staticmethod
    def _collect_steps(jobs: dict) -> tuple[list[str], list[str]]:
        step_names: list[str] = []
        run_commands: list[str] = []
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if not isinstance(step, dict):
                    continue
                name = step.get("name")
                if isinstance(name, str):
                    step_names.append(name)
                run = step.get("run")
                if isinstance(run, str):
                    run_commands.append(run)
        return step_names, run_commands

    @staticmethod
    def _collect_matrix(jobs: dict) -> tuple[list[str], list[str]]:
        keys: set[str] = set()
        values: set[str] = set()
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            strategy = job.get("strategy")
            if not isinstance(strategy, dict):
                continue
            matrix = strategy.get("matrix")
            if not isinstance(matrix, dict):
                continue
            CICDExtractor._walk_matrix(matrix, keys, values)
        return sorted(keys), sorted(values)

    @staticmethod
    def _walk_matrix(value: Any, keys: set[str], values: set[str], prefix: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                keys.add(key_text if not prefix else f"{prefix}.{key_text}")
                CICDExtractor._walk_matrix(item, keys, values, key_text)
        elif isinstance(value, list):
            for item in value:
                CICDExtractor._walk_matrix(item, keys, values, prefix)
        elif value is not None:
            values.add(str(value))

    @staticmethod
    def _empty_dataframe() -> pl.DataFrame:
        return pl.DataFrame(
            schema={
                "repo": pl.Utf8,
                "workflow_name": pl.Utf8,
                "workflow_path": pl.Utf8,
                "source_file": pl.Utf8,
                "crawl_date": pl.Date,
                "triggers": pl.List(pl.Utf8),
                "job_names": pl.List(pl.Utf8),
                "uses_matrix": pl.Boolean,
                "matrix_keys": pl.List(pl.Utf8),
                "matrix_values": pl.List(pl.Utf8),
                "uses_reusable_workflows": pl.Boolean,
                "reusable_workflows": pl.List(pl.Utf8),
                "actions_used": pl.List(pl.Utf8),
                "actions_normalized": pl.List(pl.Utf8),
                "has_permissions_block": pl.Boolean,
                "permissions": pl.Utf8,
                "runs_on": pl.List(pl.Utf8),
                "concurrency_set": pl.Boolean,
                "ai_review_actions": pl.List(pl.Utf8),
                "has_ai_review": pl.Boolean,
                "has_security_scan": pl.Boolean,
                "step_names": pl.List(pl.Utf8),
                "run_commands": pl.List(pl.Utf8),
            }
        )
