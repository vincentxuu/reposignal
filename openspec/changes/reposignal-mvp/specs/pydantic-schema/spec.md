## ADDED Requirements

### Requirement: Workflow Record Contract
The extractor SHALL validate every parsed GitHub Actions workflow against a typed workflow record contract before persisting it.

#### Scenario: Valid workflow is extracted
- **WHEN** a workflow YAML file contains valid jobs, triggers, and steps
- **THEN** the extractor persists a record containing repo, workflow identity, crawl date, triggers, jobs, actions, matrix metadata, permissions, and detection booleans

#### Scenario: Invalid workflow is skipped
- **WHEN** a workflow YAML file cannot be parsed as a top-level mapping
- **THEN** the extractor SHALL skip that file and record the parse issue without aborting the entire extraction
