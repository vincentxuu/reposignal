## 1. ETL Foundation

- [x] 1.1 Add a Pydantic workflow record contract for extractor output.
- [x] 1.2 Expand workflow extraction with source path, crawl date, matrix, reusable workflow, permissions, step name, and run command fields.
- [x] 1.3 Write latest and crawl-date partitioned Parquet outputs.
- [x] 1.4 Add incremental crawler cache support using ETag, Last-Modified, and workflow file SHA metadata.
- [x] 1.5 Add analyzer compatibility defaults for older Parquet schemas.

## 2. Intelligence Outputs

- [x] 2.1 Add CI/CD pattern detection module using the research taxonomy.
- [x] 2.2 Add weighted security posture scoring with per-dimension recommendations.
- [x] 2.3 Add workflow and pattern changelog between analysis snapshots.
- [x] 2.4 Add data quality summary for required columns and duplicate workflow rows.
- [x] 2.5 Add per-repo profile JSON generation from metadata and analysis output.
- [x] 2.6 Render pattern, security score, changelog, and quality sections in English and Traditional Chinese reports.

## 3. Automation and Documentation

- [x] 3.1 Add tests for pattern detection, security scoring, and data quality.
- [x] 3.2 Add GitHub Actions CI and optional scheduled pipeline artifact generation.
- [x] 3.3 Update README with current structured outputs and MVP coverage.
- [x] 3.4 Validate the OpenSpec change with strict validation.

## 4. Remaining Product Scope

- [x] 4.1 Split `src/analyzer.py` into focused `src/analysis/` modules without changing output compatibility.
- [x] 4.2 Add Dagster software-defined assets and Dagit-compatible local orchestration.
- [x] 4.3 Add Pandera or equivalent dataframe validation at asset boundaries.
- [x] 4.4 Add extended crawler Batch 1 for pre-commit, CODEOWNERS, SECURITY, CONTRIBUTING, Dependabot/Renovate, PR template, and issue template presence.
- [x] 4.5 Add extended crawler Batch 2 content parsers for config trends, monorepo structure, and linter configuration.
- [x] 4.6 Add extended crawler Batch 3 structure inference for release strategy, dev environment, and RFC/ADR process.
- [x] 4.7 Add Tier 3 cross-workflow inference for multi-stage release and ecosystem CI beyond current workflow-level heuristics.
- [x] 4.8 Add lineage fields from reported metrics back to raw workflow files.
- [x] 4.9 Add seed expansion workflow and comparison-by-seed-intersection trend logic.
- [x] 4.10 Build the SvelteKit/Cloudflare Pages static site for pattern library, repo pages, security dashboard, trends, and reports.
- [x] 4.11 Add Cloudflare D1/KV/R2 data publishing and SvelteKit server routes for APIs.
- [x] 4.12 Add interactive workflow diff, generator, CI copilot, migrator, flaky test detective, AI reviewer kit, and repo health check tools.
