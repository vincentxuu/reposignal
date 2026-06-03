"""Tests for lineage and seed-list trend helpers."""

from pathlib import Path

from src.lineage import build_lineage
from src.seed_management import comparison_intersection, seed_fingerprint, seed_metadata


def test_build_lineage_maps_patterns_to_source_files() -> None:
    repos = [
        {
            "repo": "a/b",
            "workflows": [
                {
                    "name": "ci",
                    "path": ".github/workflows/ci.yml",
                    "source_file": "data/raw/a/b/ci.yml",
                }
            ],
        }
    ]
    patterns = {
        "patterns": [
            {
                "slug": "security-scanning",
                "examples": [
                    {
                        "repo": "a/b",
                        "workflow": "ci",
                        "path": ".github/workflows/ci.yml",
                        "source_file": "data/raw/a/b/ci.yml",
                    }
                ],
            }
        ]
    }

    lineage = build_lineage(repos, patterns)

    assert lineage["sources_by_repo"]["a/b"] == ["data/raw/a/b/ci.yml"]
    assert lineage["pattern_sources"]["security-scanning"][0]["source_file"] == "data/raw/a/b/ci.yml"


def test_seed_metadata_is_stable_for_reordered_seed_list(tmp_path: Path) -> None:
    seed_a = [
        {"owner": "b", "repo": "two"},
        {"owner": "a", "repo": "one"},
    ]
    seed_b = list(reversed(seed_a))

    assert seed_fingerprint(seed_a) == seed_fingerprint(seed_b)

    path = tmp_path / "seed_repos.json"
    path.write_text('[{"owner":"a","repo":"one"},{"owner":"b","repo":"two"}]')
    metadata = seed_metadata(path)

    assert metadata["repo_count"] == 2
    assert metadata["repos"] == ["a/one", "b/two"]


def test_comparison_intersection_separates_seed_changes() -> None:
    result = comparison_intersection(
        previous=["a/one", "b/two"],
        current=["b/two", "c/three"],
    )

    assert result["intersection_repos"] == ["b/two"]
    assert result["previous_only"] == ["a/one"]
    assert result["current_only"] == ["c/three"]
