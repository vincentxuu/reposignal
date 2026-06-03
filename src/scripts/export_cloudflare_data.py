"""Export RepoSignal analysis into Cloudflare-oriented D1/KV/R2 artifacts."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export RepoSignal data for Cloudflare publishing.")
    parser.add_argument("--analysis", type=Path, default=Path("data/analysis/current.json"))
    parser.add_argument("--out", type=Path, default=Path("data/cloudflare"))
    args = parser.parse_args()

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)

    (args.out / "kv-analysis-current.json").write_text(
        json.dumps({"key": "analysis:current", "value": analysis}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (args.out / "r2-manifest.json").write_text(
        json.dumps({
            "objects": [
                {"key": "analysis/current.json", "path": str(args.analysis)},
                {"key": "configs/batch1.json", "path": "data/configs/batch1.json"},
                {"key": "configs/batch2.json", "path": "data/configs/batch2.json"},
                {"key": "configs/batch3.json", "path": "data/configs/batch3.json"},
            ]
        }, indent=2),
        encoding="utf-8",
    )
    (args.out / "d1.sql").write_text(_d1_sql(analysis), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "files": ["kv-analysis-current.json", "r2-manifest.json", "d1.sql"]}, indent=2))


def _d1_sql(analysis: dict) -> str:
    lines = [
        "CREATE TABLE IF NOT EXISTS repos (repo TEXT PRIMARY KEY, workflow_count INTEGER, maturity_pct INTEGER, security_score REAL);",
        "CREATE TABLE IF NOT EXISTS patterns (slug TEXT PRIMARY KEY, name TEXT, category TEXT, repo_count INTEGER, adoption_pct REAL);",
        "DELETE FROM repos;",
        "DELETE FROM patterns;",
    ]
    security = {
        item["repo"]: item.get("score")
        for item in analysis.get("security_posture", {}).get("scores", [])
    }
    for repo in analysis.get("repo_summaries", []):
        lines.append(
            "INSERT INTO repos VALUES "
            f"({_sql(repo['repo'])}, {int(repo.get('workflow_count', 0))}, {int(repo.get('maturity_pct', 0))}, {float(security.get(repo['repo']) or 0)});"
        )
    for pattern in analysis.get("pattern_detection", {}).get("patterns", []):
        lines.append(
            "INSERT INTO patterns VALUES "
            f"({_sql(pattern['slug'])}, {_sql(pattern['name'])}, {_sql(pattern['category'])}, {int(pattern.get('repo_count', 0))}, {float(pattern.get('adoption_pct', 0))});"
        )
    return "\n".join(lines) + "\n"


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


if __name__ == "__main__":
    main()
