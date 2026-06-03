"""CI/CD pattern detection based on the research taxonomy."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PatternDefinition:
    slug: str
    name: str
    category: str
    tier: int
    description: str


PATTERNS: tuple[PatternDefinition, ...] = (
    PatternDefinition("ai-code-review", "AI code review", "AI-Powered CI", 1, "AI reviewer integrated into PR workflows."),
    PatternDefinition("ai-security-review", "AI security review", "AI-Powered CI", 1, "AI-assisted security review or security-focused AI workflow."),
    PatternDefinition("ai-contribution-audit", "AI contribution audit", "AI-Powered CI", 1, "Audits AI-authored or AI-assisted contributions."),
    PatternDefinition("dogfooding", "Dogfooding", "AI-Powered CI", 2, "Workflow uses an action from the same owner/org."),
    PatternDefinition("security-scanning", "Security scanning", "Security & Supply Chain", 1, "Automated security scanners in CI."),
    PatternDefinition("container-signing", "Container signing", "Security & Supply Chain", 1, "Container or artifact signing/SBOM tooling."),
    PatternDefinition("harden-runner", "Harden runner", "Security & Supply Chain", 1, "Uses runner hardening controls."),
    PatternDefinition("least-privilege-permissions", "Least-privilege permissions", "Security & Supply Chain", 1, "Explicit GitHub token permissions."),
    PatternDefinition("hardware-matrix", "Hardware/platform matrix", "Testing Strategy", 2, "Matrix includes hardware, accelerator, arch, or OS platform coverage."),
    PatternDefinition("chaos-engineering", "Chaos engineering", "Testing Strategy", 1, "Chaos, fault injection, or resilience test tooling."),
    PatternDefinition("fuzz-randomized-testing", "Fuzz/randomized testing", "Testing Strategy", 1, "Fuzz, randomized, or property-based tests in CI."),
    PatternDefinition("flaky-test-retry", "Flaky test retry", "Testing Strategy", 2, "Retry logic for flaky tests or dedicated retry workflow."),
    PatternDefinition("performance-tracking", "Performance tracking", "Testing Strategy", 1, "Benchmarks, profiling, or perf regression checks."),
    PatternDefinition("python-future-testing", "Python future testing", "Testing Strategy", 1, "Python prerelease/free-threaded test coverage."),
    PatternDefinition("multi-stage-release", "Multi-stage release train", "Release Pipeline", 2, "Multiple release workflows or staged release jobs."),
    PatternDefinition("multi-channel-release", "Multi-channel release", "Release Pipeline", 2, "Stable/beta/canary/nightly/preview release channels."),
    PatternDefinition("pr-package-preview", "PR package preview", "Release Pipeline", 1, "Publishes preview packages for pull requests."),
    PatternDefinition("reusable-workflows", "Reusable workflows", "Workflow Architecture", 1, "Uses reusable workflow calls."),
    PatternDefinition("multiple-build-systems", "Multiple build systems", "Workflow Architecture", 2, "CI invokes multiple build systems in one repo."),
    PatternDefinition("per-sample-ci", "Per-sample CI", "Workflow Architecture", 2, "Many workflows appear dedicated to samples/examples/docs."),
    PatternDefinition("ecosystem-ci", "Ecosystem CI", "Ecosystem Integration", 2, "Workflow triggers downstream/ecosystem compatibility checks."),
    PatternDefinition("cross-version-compat", "Cross-version compatibility", "Cross-version Compat", 1, "Matrix spans at least three runtime versions."),
)

DEFINITIONS_BY_SLUG = {pattern.slug: pattern for pattern in PATTERNS}

SECURITY_RE = re.compile(r"trivy|snyk|grype|codeql|semgrep|gitleaks|scorecard|gosec|osv-scanner", re.I)
SUPPLY_CHAIN_RE = re.compile(r"cosign|sigstore|syft|sbom|slsa|provenance|attest|dependency-review", re.I)
CHAOS_RE = re.compile(r"chaos|fault|toxiproxy|litmus|pod[-_ ]?kill|network partition", re.I)
FUZZ_RE = re.compile(r"fuzz|randomi[sz]ed|property[-_ ]?based|hypothesis|quickcheck|miri", re.I)
PERF_RE = re.compile(r"benchmark|bench|callgrind|valgrind|perf|profil", re.I)
RETRY_RE = re.compile(r"retry|flaky|rerun|nick-fields/retry|action-retry", re.I)
AI_RE = re.compile(r"claude|copilot|openai|codex|ai[-_ ]?review|coderabbit|sourcery", re.I)
AI_AUDIT_RE = re.compile(r"check[-_ ]?ai[-_ ]?coauthors|ai[-_ ]?co[-_ ]?authors|ai contribution", re.I)
PREVIEW_PACKAGE_RE = re.compile(r"pkg\.pr\.new|preview package|pr package", re.I)
RELEASE_RE = re.compile(r"release|publish|promote|deploy", re.I)
CHANNEL_RE = re.compile(r"stable|beta|alpha|canary|nightly|preview|next", re.I)
ECOSYSTEM_RE = re.compile(r"ecosystem|downstream|compatibility|primer|nuxt|vite|router|plugin", re.I)
BUILD_SYSTEMS = ("bazel", "buck2", "nix", "make", "cmake", "gradle", "maven", "cargo", "pnpm", "npm", "yarn", "bun", "uv", "poetry")
HARDWARE_TERMS = ("cuda", "gpu", "tpu", "npu", "xpu", "hpu", "amd", "arm64", "aarch64", "x86", "blackwell", "xeon", "h20")


def detect_patterns(repo_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect research-backed CI/CD patterns from per-repo workflow summaries."""
    pattern_map: dict[str, dict[str, Any]] = {
        p.slug: {
            "slug": p.slug,
            "name": p.name,
            "category": p.category,
            "tier": p.tier,
            "description": p.description,
            "repo_count": 0,
            "workflow_count": 0,
            "repos": [],
            "examples": [],
        }
        for p in PATTERNS
    }

    for repo in repo_summaries:
        repo_hits: set[str] = set()
        owner = repo["repo"].split("/", 1)[0].lower()
        repo_text = _repo_text(repo)
        build_system_hits = {term for term in BUILD_SYSTEMS if re.search(rf"\b{re.escape(term)}\b", repo_text, re.I)}
        release_workflows: list[dict[str, Any]] = []
        sample_workflow_count = 0
        dispatch_like_workflows = 0

        for workflow in repo.get("workflows", []):
            text = _workflow_text(workflow)
            actions = [a.lower() for a in workflow.get("actions", [])]
            slugs: set[str] = set()
            if workflow.get("has_ai_review") or AI_RE.search(text):
                slugs.add("ai-code-review")
            if (workflow.get("has_ai_review") or AI_RE.search(text)) and re.search("security|vulnerab|threat|audit", text, re.I):
                slugs.add("ai-security-review")
            if AI_AUDIT_RE.search(text):
                slugs.add("ai-contribution-audit")
            if workflow.get("has_security_scan") or SECURITY_RE.search(text):
                slugs.add("security-scanning")
            if SUPPLY_CHAIN_RE.search(text):
                slugs.add("container-signing")
            if any("step-security/harden-runner" in a for a in actions):
                slugs.add("harden-runner")
            if workflow.get("has_permissions"):
                slugs.add("least-privilege-permissions")
            if _has_hardware_matrix(workflow):
                slugs.add("hardware-matrix")
            if CHAOS_RE.search(text):
                slugs.add("chaos-engineering")
            if FUZZ_RE.search(text):
                slugs.add("fuzz-randomized-testing")
            if RETRY_RE.search(text):
                slugs.add("flaky-test-retry")
            if PERF_RE.search(text):
                slugs.add("performance-tracking")
            if _has_python_future_testing(workflow):
                slugs.add("python-future-testing")
            if RELEASE_RE.search(workflow.get("name", "")) or RELEASE_RE.search(text):
                release_workflows.append(workflow)
            if _has_dispatch_or_workflow_dependency(workflow):
                dispatch_like_workflows += 1
            if RELEASE_RE.search(text) and CHANNEL_RE.search(text):
                slugs.add("multi-channel-release")
            if PREVIEW_PACKAGE_RE.search(text):
                slugs.add("pr-package-preview")
            if workflow.get("uses_reusable_workflows"):
                slugs.add("reusable-workflows")
            if ECOSYSTEM_RE.search(text):
                slugs.add("ecosystem-ci")
            if _has_cross_version_compat(workflow):
                slugs.add("cross-version-compat")
            if _is_sample_workflow(workflow):
                sample_workflow_count += 1
            if any(a.startswith(f"{owner}/") for a in actions):
                slugs.add("dogfooding")

            for slug in slugs:
                _add_workflow_hit(pattern_map[slug], repo["repo"], workflow)
            repo_hits.update(slugs)

        if len(release_workflows) >= 3 or (len(release_workflows) >= 2 and dispatch_like_workflows > 0):
            _add_repo_hit(
                pattern_map["multi-stage-release"],
                repo["repo"],
                {"workflows": [wf.get("name", "") for wf in release_workflows[:5]]},
            )
            repo_hits.add("multi-stage-release")
        if len(build_system_hits) >= 3:
            _add_repo_hit(pattern_map["multiple-build-systems"], repo["repo"], {"systems": sorted(build_system_hits)})
            repo_hits.add("multiple-build-systems")
        if repo.get("workflow_count", 0) >= 10 and sample_workflow_count >= 3:
            _add_repo_hit(pattern_map["per-sample-ci"], repo["repo"], {"sample_workflows": sample_workflow_count})
            repo_hits.add("per-sample-ci")

        repo["pattern_slugs"] = sorted(repo_hits)
        repo["pattern_count"] = len(repo_hits)

    for item in pattern_map.values():
        item["repo_count"] = len(set(item["repos"]))
        item["adoption_pct"] = 0.0
        if repo_summaries:
            item["adoption_pct"] = round(item["repo_count"] / len(repo_summaries) * 100, 2)
        item["repos"] = sorted(set(item["repos"]))
        item["examples"] = item["examples"][:5]

    categories: dict[str, dict[str, Any]] = {}
    for item in pattern_map.values():
        category = categories.setdefault(item["category"], {"category": item["category"], "repo_count": 0, "patterns": []})
        category["patterns"].append(item)
    for category in categories.values():
        category["repo_count"] = len({repo for pattern in category["patterns"] for repo in pattern["repos"]})
        category["patterns"].sort(key=lambda p: (-p["repo_count"], p["name"]))

    return {
        "total_patterns": len(PATTERNS),
        "detected_patterns": sum(1 for item in pattern_map.values() if item["repo_count"] > 0),
        "patterns": sorted(pattern_map.values(), key=lambda p: (-p["repo_count"], p["category"], p["name"])),
        "categories": sorted(categories.values(), key=lambda c: c["category"]),
    }


def _add_workflow_hit(pattern: dict[str, Any], repo: str, workflow: dict[str, Any]) -> None:
    pattern["workflow_count"] += 1
    pattern["repos"].append(repo)
    if len(pattern["examples"]) < 5:
        pattern["examples"].append({
            "repo": repo,
            "workflow": workflow.get("name", ""),
            "path": workflow.get("path", ""),
            "source_file": workflow.get("source_file", ""),
        })


def _add_repo_hit(pattern: dict[str, Any], repo: str, extra: dict[str, Any] | None = None) -> None:
    pattern["repos"].append(repo)
    if len(pattern["examples"]) < 5:
        pattern["examples"].append({"repo": repo, **(extra or {})})


def _repo_text(repo: dict[str, Any]) -> str:
    parts: list[str] = []
    for workflow in repo.get("workflows", []):
        parts.append(_workflow_text(workflow))
    return "\n".join(parts)


def _workflow_text(workflow: dict[str, Any]) -> str:
    fields = [
        workflow.get("name", ""),
        " ".join(workflow.get("triggers", [])),
        " ".join(workflow.get("jobs", [])),
        " ".join(workflow.get("actions", [])),
        " ".join(workflow.get("notable_actions", [])),
        " ".join(workflow.get("runs_on", [])),
        " ".join(workflow.get("matrix_keys", [])),
        " ".join(workflow.get("matrix_values", [])),
        " ".join(workflow.get("step_names", [])),
        " ".join(workflow.get("run_commands", [])),
        " ".join(workflow.get("reusable_workflows", [])),
    ]
    return "\n".join(fields)


def _has_hardware_matrix(workflow: dict[str, Any]) -> bool:
    if not workflow.get("uses_matrix"):
        return False
    values = [*workflow.get("matrix_keys", []), *workflow.get("matrix_values", []), *workflow.get("runs_on", [])]
    return any(term in str(value).lower() for term in HARDWARE_TERMS for value in values)


def _has_python_future_testing(workflow: dict[str, Any]) -> bool:
    values = [str(v).lower() for v in workflow.get("matrix_values", [])]
    text = _workflow_text(workflow).lower()
    return any("3.14" in v or "free-threaded" in v for v in values) or ("3.14" in text and "python" in text)


def _has_cross_version_compat(workflow: dict[str, Any]) -> bool:
    versions = set()
    for value in workflow.get("matrix_values", []):
        if re.fullmatch(r"v?\d+(?:\.\d+){0,2}", str(value)):
            versions.add(str(value))
    return len(versions) >= 3


def _is_sample_workflow(workflow: dict[str, Any]) -> bool:
    text = _workflow_text(workflow)
    return bool(re.search(r"sample|example|docs?|tutorial|cookbook", text, re.I))


def _has_dispatch_or_workflow_dependency(workflow: dict[str, Any]) -> bool:
    triggers = {str(trigger).lower() for trigger in workflow.get("triggers", [])}
    text = _workflow_text(workflow).lower()
    return bool(
        {"workflow_run", "workflow_dispatch", "repository_dispatch"} & triggers
        or "gh workflow run" in text
        or "repository_dispatch" in text
        or "workflow_run" in text
    )
