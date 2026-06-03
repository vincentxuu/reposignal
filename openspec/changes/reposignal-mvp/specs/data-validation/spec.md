## ADDED Requirements

### Requirement: Data Quality Summary
The analyzer SHALL produce data quality metrics for every analysis run.

#### Scenario: Required columns are missing
- **WHEN** the processed workflow dataset is missing expected columns
- **THEN** the data quality summary SHALL report the missing columns and fail or warn the quality status

#### Scenario: Duplicate workflow rows exist
- **WHEN** multiple rows share the same repo, workflow name, and workflow path
- **THEN** the data quality summary SHALL report the duplicate count
