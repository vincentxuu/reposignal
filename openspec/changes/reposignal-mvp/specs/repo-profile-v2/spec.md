## ADDED Requirements

### Requirement: CI/CD Profile Summary
The repo profile SHALL include CI/CD summary fields derived from the analysis output.

#### Scenario: Repository has analysis results
- **WHEN** a repository has workflow count, detected patterns, security score, and maturity percentage
- **THEN** its profile SHALL include those fields under a CI/CD summary object
