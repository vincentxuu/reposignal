"""Security posture scoring for repositories."""

from __future__ import annotations

import re
from typing import Any


SECURITY_TOOL_RE = re.compile(r"trivy|snyk|grype|codeql|semgrep|gitleaks|scorecard|gosec|osv-scanner", re.I)
SUPPLY_CHAIN_RE = re.compile(r"cosign|sigstore|syft|sbom|slsa|provenance|attest|dependency-review", re.I)
APP_TOKEN_RE = re.compile(r"create-github-app-token|github app token|app-token|installation token", re.I)
PAT_RE = re.compile(r"\bPAT\b|personal access token|GH_TOKEN|GITHUB_TOKEN", re.I)


def score_security_posture(repo_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Return weighted security scores and recommendations for each repo."""
    scores = []
    for repo in repo_summaries:
        workflows = repo.get("workflows", [])
        workflow_count = len(workflows)
        explicit_permissions = sum(1 for wf in workflows if wf.get("has_permissions"))
        permissions_rate = explicit_permissions / workflow_count if workflow_count else 0.0

        all_actions = sorted({a for wf in workflows for a in wf.get("actions", [])})
        all_text = "\n".join(
            " ".join([
                wf.get("name", ""),
                " ".join(wf.get("actions", [])),
                " ".join(wf.get("run_commands", [])),
                " ".join(wf.get("step_names", [])),
            ])
            for wf in workflows
        )

        security_tools = sorted({a for a in all_actions if SECURITY_TOOL_RE.search(a)})
        supply_chain_tools = sorted({a for a in all_actions if SUPPLY_CHAIN_RE.search(a)} | set(SUPPLY_CHAIN_RE.findall(all_text)))
        has_harden_runner = any("step-security/harden-runner" in a.lower() for a in all_actions)
        has_app_token = bool(APP_TOKEN_RE.search(all_text))
        mentions_pat = bool(PAT_RE.search(all_text))

        dimensions = {
            "permissions": round(permissions_rate * 25, 2),
            "security_scan": round(min(len(security_tools), 6) / 6 * 25, 2),
            "supply_chain": round(min(len(supply_chain_tools), 3) / 3 * 20, 2),
            "secret_handling": 15.0 if has_app_token and not mentions_pat else 7.5 if has_app_token else 0.0,
            "harden_runner": 15.0 if has_harden_runner else 0.0,
        }
        total = round(sum(dimensions.values()), 2)
        recommendations = []
        if permissions_rate < 1:
            recommendations.append("Set explicit `permissions:` in every workflow.")
        if not security_tools:
            recommendations.append("Add at least one CI security scanner such as CodeQL, Trivy, Semgrep, Gitleaks, or Scorecard.")
        if not supply_chain_tools:
            recommendations.append("Add supply-chain controls such as SBOM generation, artifact attestation, dependency review, or cosign signing.")
        if not has_app_token:
            recommendations.append("Prefer GitHub App installation tokens for automation that needs write access.")
        if not has_harden_runner:
            recommendations.append("Consider `step-security/harden-runner` for sensitive workflows.")

        scores.append({
            "repo": repo["repo"],
            "url": repo["url"],
            "score": total,
            "dimensions": dimensions,
            "security_tools": security_tools,
            "supply_chain_tools": supply_chain_tools,
            "recommendations": recommendations,
        })

    scores.sort(key=lambda item: (-item["score"], item["repo"]))
    average = round(sum(item["score"] for item in scores) / len(scores), 2) if scores else 0.0
    return {
        "average_score": average,
        "top": scores[:10],
        "bottom": list(reversed(scores[-10:])) if scores else [],
        "scores": scores,
    }
