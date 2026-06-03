## ADDED Requirements

### Requirement: Focused Regression Tests
The project SHALL include tests for crawler behavior, extractor parsing, analyzer output, reporter rendering, pattern detection, security scoring, and data quality checks.

#### Scenario: Test suite runs
- **WHEN** `uv run python -m pytest tests/ -q` is executed
- **THEN** the suite SHALL complete successfully without network access
