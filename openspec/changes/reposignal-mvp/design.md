## Context

RepoSignal started as a local Python pipeline that crawls GitHub Actions workflow
YAML, extracts a single Parquet dataset, runs DuckDB analysis, and renders
bilingual Markdown reports. The proposal expands this into a sustained product:
versioned seed repos, regular ETL, structured pattern detection from the
research taxonomy, security scoring, changelog/history, repo profiles, and later
a SvelteKit/Cloudflare public surface.

Current constraints:

- The Python pipeline is the source of truth for crawl, extract, analysis, and
  report generation.
- `seed_repos.json` and `seed_repos_metadata.json` are the controlled seed-list
  inputs.
- Reports and JSON outputs must be useful without the future website.
- Long-running crawl work must conserve GitHub API quota.
- Historical comparisons require stable seed-list and snapshot metadata.

## Goals / Non-Goals

**Goals:**

- Stabilize the local ETL pipeline with schema contracts, partitioned snapshots,
  quality checks, and repeatable tests.
- Convert the research document's CI/CD patterns into structured detection
  output that reports and future site pages can consume.
- Add security posture scoring and repo profile JSON as first-class outputs.
- Add workflow/pattern changelog support between analysis snapshots.
- Add GitHub Actions automation for tests and optional scheduled pipeline runs.
- Keep later Dagster, extended crawlers, site, Cloudflare storage, and
  self-service tooling represented as explicit follow-up tasks instead of
  implicit hidden work.

**Non-Goals:**

- Do not build the SvelteKit/Cloudflare site in the Python package itself.
- Do not require LLM calls for the baseline repo profile; deterministic metadata
  summaries are acceptable until an LLM provider is configured.
- Do not mutate the seed list automatically from search results; candidate
  generation remains separate from the committed seed list.

## Decisions

### Decision: Keep the Python pipeline as the canonical analysis engine

The first product milestone should deepen the existing working pipeline rather
than replace it. The analyzer returns one structured JSON payload containing
statistics, pattern detection, security scores, changelog, quality, and repo
summaries. Reports, generated profiles, and the future website should consume
that payload.

Alternative considered: immediately move orchestration to Dagster. This is still
part of the roadmap, but it is not a prerequisite for making the current
pipeline valuable and testable.

### Decision: Use Pydantic for row-level workflow contracts

The extractor validates each parsed workflow through a Pydantic model before it
is written to Parquet. This catches schema drift close to the YAML parsing
boundary and documents the data contract between crawler, extractor, analyzer,
and downstream reports.

Alternative considered: rely on Polars schema inference only. That is faster to
write but weaker for explicit validation and harder to extend safely.

### Decision: Write both latest and partitioned Parquet snapshots

`data/processed/cicd.parquet` remains the latest snapshot for compatibility with
existing analyzer/report code. The extractor also writes
`data/processed/crawl_date=YYYY-MM-DD/cicd.parquet` so historical queries and
changelog work can evolve without breaking the current entrypoint.

Alternative considered: only write partitioned data and update every consumer at
once. Keeping latest plus partitioned output reduces migration risk.

### Decision: Implement pattern detection as a pure Python module

Pattern detection is implemented in `src/patterns.py` against normalized
per-repo workflow summaries. The detector encodes the 7-category taxonomy and
records adoption counts and examples. This keeps the logic deterministic,
unit-testable, and independent from DuckDB SQL complexity.

Alternative considered: express all pattern detection in SQL. SQL works for
simple action counts but becomes awkward for cross-field keyword and matrix
heuristics.

### Decision: Keep security scoring deterministic and transparent

Security scoring uses the proposal's five weighted dimensions: explicit
permissions, security scans, supply-chain controls, secret handling, and
harden-runner. Each score includes per-dimension values and recommended next
steps so users can see how to improve.

Alternative considered: ML/LLM scoring. That would be harder to verify and
unnecessary for the first useful version.

### Decision: GitHub Actions publishes artifacts, not commits generated data

The scheduled workflow runs tests and can run the pipeline on schedule or manual
dispatch, then uploads generated reports and data as artifacts. Committing
generated reports back to the repo can be added later once publish policy and
site deployment are defined.

Alternative considered: auto-commit generated outputs. This creates noisy git
history and can mask seed-list changes unless versioning policy is finalized.

## Risks / Trade-offs

- Pattern heuristics can produce false positives. Mitigation: expose examples
  and keep detector rules in a dedicated module with focused tests.
- Pydantic adds a dependency and small extraction overhead. Mitigation: validate
  one workflow record at a time and keep the model simple.
- Changelog based on analysis snapshots is weaker than raw-file diffs.
  Mitigation: retain source file paths and partitioned snapshots now; expand to
  raw-file lineage in later tasks.
- GitHub API conditional requests depend on upstream headers and local cache
  freshness. Mitigation: also use workflow file SHA metadata when available.
- The full OpenSpec proposal is larger than the current implemented slice.
  Mitigation: tasks explicitly separate completed MVP-core work from remaining
  Dagster/site/extended-crawler/tooling work.

## Migration Plan

1. Keep existing `run.py` entrypoint and `data/processed/cicd.parquet` output.
2. Add new fields to extracted records while keeping analyzer defaults for older
   Parquet fixtures.
3. Add structured analysis sections to the JSON payload and reports.
4. Add tests for new deterministic modules.
5. Add GitHub Actions CI and optional scheduled pipeline artifact generation.
6. Later, introduce Dagster assets around the same module boundaries.

Rollback strategy: the old report sections continue to read from the same
top-level keys, so new sections can be removed from templates without breaking
the crawl/extract/analyze pipeline.
