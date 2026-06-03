"""Shared data contracts for the RepoSignal pipeline."""

from datetime import date
from pydantic import BaseModel, Field


class WorkflowRecord(BaseModel):
    """Contract for one parsed GitHub Actions workflow."""

    repo: str
    workflow_name: str
    workflow_path: str
    source_file: str
    crawl_date: date
    triggers: list[str] = Field(default_factory=list)
    job_names: list[str] = Field(default_factory=list)
    uses_matrix: bool = False
    matrix_keys: list[str] = Field(default_factory=list)
    matrix_values: list[str] = Field(default_factory=list)
    uses_reusable_workflows: bool = False
    reusable_workflows: list[str] = Field(default_factory=list)
    actions_used: list[str] = Field(default_factory=list)
    actions_normalized: list[str] = Field(default_factory=list)
    has_permissions_block: bool = False
    permissions: str | None = None
    runs_on: list[str] = Field(default_factory=list)
    concurrency_set: bool = False
    ai_review_actions: list[str] = Field(default_factory=list)
    has_ai_review: bool = False
    has_security_scan: bool = False
    step_names: list[str] = Field(default_factory=list)
    run_commands: list[str] = Field(default_factory=list)
