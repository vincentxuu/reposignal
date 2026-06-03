## ADDED Requirements

### Requirement: Snapshot Changelog
The analyzer SHALL compare the current analysis snapshot with the previous analysis snapshot and summarize workflow and pattern changes.

#### Scenario: Workflow was added
- **WHEN** a workflow appears in the current snapshot but not in the previous snapshot
- **THEN** the changelog SHALL list that repository and workflow as added

#### Scenario: Pattern adoption changed
- **WHEN** a repository's detected pattern slugs differ between snapshots
- **THEN** the changelog SHALL list added and removed pattern slugs for that repository
