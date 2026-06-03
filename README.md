# RepoSignal

Engineering intelligence from open source repos. Crawls GitHub Actions workflows from top open-source repos, extracts structured data, and generates intelligence briefs with insights and recommendations.

## Quick Start

```bash
# Install dependencies
uv sync

# Set up GitHub token (no scopes needed for public repos)
cp .env.example .env
# Edit .env and fill in your GITHUB_TOKEN

# Run the full pipeline: crawl → extract → analyze → report
uv run python run.py
```

Reports are generated in `reports/`:
- `patterns-YYYY-MM-DD-HHMMSS.md` — English
- `patterns-YYYY-MM-DD-HHMMSS-zh-tw.md` — Traditional Chinese

Structured outputs are generated under `data/`:
- `data/processed/cicd.parquet` — latest workflow snapshot
- `data/processed/crawl_date=YYYY-MM-DD/cicd.parquet` — historical partition
- `data/analysis/current.json` — analysis payload for reports/sites
- `data/configs/batch1.json` — Batch 1 beyond-CI repo file-presence signals
- `data/configs/batch2.json` — Batch 2 parsed config trend signals
- `data/configs/batch3.json` — Batch 3 release/DX/RFC structural signals
- `data/profiles/*.json` — per-repo profile records

## Usage

### Full pipeline

```bash
uv run python run.py
```

Runs the pipeline sequentially: crawl workflows (GitHub API) → crawl Batch 1 repo signals → crawl Batch 2 config trends → crawl Batch 3 structural signals → extract (YAML → Parquet) → analyze (DuckDB queries + analysis modules) → report (Jinja2 markdown).

### Re-analyze without re-crawling

If you already have raw data in `data/raw/` and just want to re-run extraction, analysis, and report generation:

```bash
uv run python -c "
from src.extractors.cicd import CICDExtractor
from src.analyzer import analyze
from src.reporter import generate_report
from pathlib import Path

CICDExtractor().extract(raw_dir=Path('data/raw'))
results = analyze()
generate_report(results)
"
```

### Build seed list

Generate `seed_repos.json` from the GitHub Search API:

```bash
uv run python src/scripts/build_seed_list.py
```

### Compare seed-list versions

Trend comparisons should use the repo intersection between seed-list versions:

```bash
uv run python -m src.scripts.seed_diff data/seeds/seed_repos-OLD.json seed_repos.json
```

### Run tests

```bash
uv run python -m pytest tests/ -v
```

### Run with Dagster

```bash
uv run dagster dev -f src/dagster_defs.py
```

The Dagster asset graph wraps the same pipeline modules:
`raw_workflows → extended_batch1 → extended_batch2 → extended_batch3 → cicd_parquet → analysis_json → report_markdown`.
The `cicd_parquet` asset validates the dataframe contract before downstream
analysis runs.

### Run the SvelteKit site

```bash
cd site
npm install
npm run dev -- --port 5177
```

The site uses `@sveltejs/adapter-cloudflare` and includes dashboard, pattern
library, security, trends, reports, repo profile pages, and API routes prepared
for Cloudflare D1/KV/R2 bindings.

Cloudflare export artifacts can be generated with:

```bash
uv run python -m src.scripts.export_cloudflare_data
```

## Architecture

```
seed_repos.json
       |
       v
 +-----------+     +------------+     +-----------+     +-----------+     +-----------+
 |  Crawler  | --> | ExtCrawler | --> | Extractor | --> | Analyzer  | --> | Reporter  |
 +-----------+     +------------+     +-----------+     +-----------+     +-----------+
  workflows        repo signals       YAML parse       DuckDB + modules  Jinja2 markdown
  data/raw/        data/configs/      data/processed/  data/analysis/    reports/
```

- **Crawler** — async GitHub Contents API fetcher with rate-limit backoff
- **Extended Crawler** — Batch 1 beyond-CI file-presence observer
- **Extractor** — parses workflow YAML into structured Polars DataFrame, outputs Parquet
- **Analyzer** — orchestration layer over DuckDB queries and focused `src/analysis/` modules
- **Reporter** — Jinja2 templates producing bilingual intelligence briefs (EN + ZH-TW)
- **Dagster definitions** — asset graph for local Dagit monitoring and single-asset reruns

## What the report covers

1. **Matrix Strategy Usage** — multi-platform/multi-version testing adoption
2. **Top GitHub Actions** — categorized by purpose (CI/Build, Security, Docker, Cache, AI, etc.); the report currently surfaces the top 50
3. **AI Code Review Adoption** — repos using Claude, Copilot, or other AI reviewers
4. **Security Posture** — explicit permissions + automated security scanning
5. **Workflow Fingerprints** — common action combinations ("recipes") across repos
6. **Key Insights** — human-readable interpretation of each metric
7. **Recommendations** — actionable steps based on ecosystem patterns

## Project Structure

```
reposignal/
  run.py                  # Pipeline entrypoint
  seed_repos.json         # Input: list of repos to analyze
  src/
    crawler.py            # Stage 1: fetch workflow files
    extended_crawler.py   # Stage 1b: beyond-CI Batch 1 file presence
    extractors/
      cicd.py             # Stage 2: YAML → Parquet
    analysis/             # Focused analysis helpers
    analyzer.py           # Stage 3: analysis orchestration
    dagster_defs.py       # Dagster asset graph
    validation.py         # Dataframe validation boundaries
    reporter.py           # Stage 4: report generation
    templates/
      report.md.j2        # English report template
      report-zh-tw.md.j2  # Traditional Chinese report template
    scripts/
      build_seed_list.py  # Seed list builder
  data/
    raw/                  # Raw YAML files per repo
    processed/            # latest + crawl_date-partitioned cicd.parquet
    analysis/             # current.json, previous.json
    configs/              # beyond-CI observation outputs
    profiles/             # per-repo profile JSON
  reports/                # Generated markdown reports
  tests/                  # pytest test suite
```

## Tech Stack

Python 3.12+ / httpx / Polars / DuckDB / Jinja2 / uv

## MVP Coverage

The current implementation covers the core local intelligence pipeline:

- Schema-validated workflow records via Pydantic
- Incremental crawler cache using ETag/Last-Modified and file SHA metadata
- Partitioned Parquet snapshots by `crawl_date`
- Research-backed CI/CD pattern detection across the 7-category taxonomy
- Weighted security posture scoring
- Workflow and pattern changelog between analysis snapshots
- Data quality summary for schema and duplicate checks
- Lineage maps from workflows and detected patterns back to raw source files
- Seed-list fingerprint and intersection helpers for trend comparisons that
  control for changing repo sets
- Dagster asset graph with dataframe validation before analysis
- Repo profile JSON generation
- GitHub Actions CI plus optional weekly/manual pipeline artifact generation
- Batch 1 beyond-CI file-presence observation for pre-commit, CODEOWNERS,
  security policy, contributing docs, dependency automation, PR templates, and
  issue templates
- Batch 2 config parsing for `tsconfig.json`, `pyproject.toml`, `Cargo.toml`,
  `turbo.json`, `nx.json`, `pnpm-workspace.yaml`, ESLint, Ruff, and Biome
- Batch 3 structure inference for release strategy, development environment,
  and RFC/ADR decision-process signals
- SvelteKit + Cloudflare Pages product surface with pattern library, repo pages,
  security dashboard, trends, reports, and starter API routes
- Interactive tools page and APIs for workflow diff, workflow generator
  (Python, Node, Rust, Go, Java, and Docker stacks), CI copilot recommendations,
  workflow migrator, flaky test detective, AI reviewer kit, and repo health check
  (snapshot lookup with live GitHub fallback for arbitrary repos)

Live arbitrary-repo health checks are implemented (with optional `GITHUB_TOKEN` auth from the Cloudflare environment to lift the unauthenticated rate limit), and the workflow generator covers Python, Node, Rust, Go, Java, and Docker stacks. Remaining production hardening is deployment-specific: wiring real Cloudflare resource IDs into `site/wrangler.toml` (currently placeholder zeros, requires a Cloudflare account) and request-level rate limiting backed by Cloudflare KV.
