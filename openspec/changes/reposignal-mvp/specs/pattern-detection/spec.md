## ADDED Requirements

### Requirement: Research Pattern Taxonomy
The analyzer SHALL convert workflow records into structured CI/CD pattern adoption data based on the research taxonomy categories.

#### Scenario: Pattern appears in workflows
- **WHEN** workflows contain matching actions, matrix values, step names, commands, or reusable workflow calls
- **THEN** the analyzer SHALL report the matching pattern slug, category, tier, repo count, workflow count, adoption percentage, and examples

#### Scenario: No repo adopts a pattern
- **WHEN** no workflows match a tracked pattern
- **THEN** the analyzer SHALL keep the pattern in the taxonomy output with zero adoption
