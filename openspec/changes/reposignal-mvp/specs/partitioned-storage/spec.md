## ADDED Requirements

### Requirement: Latest and Historical Parquet Outputs
The extractor SHALL persist both a latest Parquet snapshot and a crawl-date partitioned Parquet snapshot.

#### Scenario: Extraction completes
- **WHEN** workflow extraction finishes for a crawl date
- **THEN** the system SHALL write `data/processed/cicd.parquet` and `data/processed/crawl_date=YYYY-MM-DD/cicd.parquet`
