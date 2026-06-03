## ADDED Requirements

### Requirement: Weighted Security Score
The analyzer SHALL compute a per-repository security posture score from explicit permissions, security scanners, supply-chain controls, secret handling, and runner hardening.

#### Scenario: Repository uses strong controls
- **WHEN** a repository has explicit workflow permissions, multiple security scanners, supply-chain tooling, GitHub App token automation, and harden-runner
- **THEN** the analyzer SHALL assign a high score and expose the per-dimension contribution

#### Scenario: Repository is missing controls
- **WHEN** a repository lacks one or more security controls
- **THEN** the analyzer SHALL include concrete recommendations for the missing dimensions
