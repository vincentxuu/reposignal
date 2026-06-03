"""Compare seed-list versions using repo-set intersection semantics."""

import argparse
import json
from pathlib import Path

from src.seed_management import comparison_intersection, seed_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two RepoSignal seed lists.")
    parser.add_argument("previous", type=Path, help="Previous seed_repos.json")
    parser.add_argument("current", type=Path, help="Current seed_repos.json")
    args = parser.parse_args()

    previous = seed_metadata(args.previous)
    current = seed_metadata(args.current)
    comparison = comparison_intersection(previous["repos"], current["repos"])
    print(json.dumps({
        "previous": {
            "file": previous["seed_file"],
            "repo_count": previous["repo_count"],
            "fingerprint": previous["fingerprint"],
        },
        "current": {
            "file": current["seed_file"],
            "repo_count": current["repo_count"],
            "fingerprint": current["fingerprint"],
        },
        "comparison": comparison,
    }, indent=2))


if __name__ == "__main__":
    main()
