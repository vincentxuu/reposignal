## ADDED Requirements

### Requirement: Conditional GitHub Fetching
The crawler SHALL avoid unnecessary GitHub API downloads by reusing cached HTTP validators and workflow file metadata.

#### Scenario: Repository workflow listing is unchanged
- **WHEN** GitHub returns `304 Not Modified` for a workflow listing request
- **THEN** the crawler SHALL count the repository as unchanged and continue without redownloading workflow files

#### Scenario: Workflow file SHA is unchanged
- **WHEN** the GitHub Contents API returns the same SHA for a workflow file already present on disk
- **THEN** the crawler SHALL count the file as unchanged and keep the local copy
