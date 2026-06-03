"""Parsers for Batch 2 engineering configuration trend extraction."""

from __future__ import annotations

import json
import re
import tomllib
from typing import Any

import yaml


def parse_json_like(text: str) -> dict[str, Any]:
    """Parse JSON/JSONC with simple comment and trailing-comma tolerance."""
    stripped = re.sub(r"//.*?$|/\*.*?\*/", "", text, flags=re.MULTILINE | re.DOTALL)
    stripped = re.sub(r",(\s*[}\]])", r"\1", stripped)
    return json.loads(stripped)


def parse_tsconfig(text: str) -> dict[str, Any]:
    data = parse_json_like(text)
    compiler = data.get("compilerOptions", {}) if isinstance(data, dict) else {}
    return {
        "extends": data.get("extends") if isinstance(data, dict) else None,
        "strict": compiler.get("strict"),
        "module": compiler.get("module"),
        "target": compiler.get("target"),
        "module_resolution": compiler.get("moduleResolution"),
        "jsx": compiler.get("jsx"),
        "paths_configured": bool(compiler.get("paths")),
    }


def parse_pyproject(text: str) -> dict[str, Any]:
    data = tomllib.loads(text)
    project = data.get("project", {})
    build_system = data.get("build-system", {})
    tools = data.get("tool", {})
    return {
        "project_name": project.get("name"),
        "requires_python": project.get("requires-python"),
        "build_backend": build_system.get("build-backend"),
        "uses_ruff": "ruff" in tools,
        "uses_pytest": "pytest" in tools,
        "uses_uv": "uv" in tools,
    }


def parse_cargo_toml(text: str) -> dict[str, Any]:
    data = tomllib.loads(text)
    return {
        "workspace": "workspace" in data,
        "package_name": data.get("package", {}).get("name"),
        "edition": data.get("package", {}).get("edition"),
        "workspace_members": len(data.get("workspace", {}).get("members", [])) if isinstance(data.get("workspace"), dict) else 0,
    }


def parse_pnpm_workspace(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text) or {}
    packages = data.get("packages", []) if isinstance(data, dict) else []
    return {
        "workspace": True,
        "package_patterns": packages,
        "package_pattern_count": len(packages),
    }


def parse_turbo_json(text: str) -> dict[str, Any]:
    data = parse_json_like(text)
    tasks = data.get("tasks") or data.get("pipeline") or {}
    return {
        "task_count": len(tasks) if isinstance(tasks, dict) else 0,
        "uses_remote_cache": bool(data.get("remoteCache")) if isinstance(data, dict) else False,
    }


def parse_nx_json(text: str) -> dict[str, Any]:
    data = parse_json_like(text)
    plugins = data.get("plugins", []) if isinstance(data, dict) else []
    return {
        "plugins": plugins,
        "plugin_count": len(plugins) if isinstance(plugins, list) else 0,
        "named_inputs": sorted((data.get("namedInputs") or {}).keys()) if isinstance(data.get("namedInputs"), dict) else [],
    }


def parse_linter_config(path: str, text: str) -> dict[str, Any]:
    lower = path.lower()
    if lower.endswith((".json", ".jsonc")) or "biome.json" in lower or "eslint" in lower:
        try:
            data = parse_json_like(text)
        except json.JSONDecodeError:
            data = {}
    elif lower.endswith((".yaml", ".yml")):
        data = yaml.safe_load(text) or {}
    elif lower.endswith(".toml"):
        data = tomllib.loads(text)
    else:
        data = {}
    return {
        "path": path,
        "top_level_keys": sorted(data.keys()) if isinstance(data, dict) else [],
        "rule_count": _rule_count(data),
    }


def parse_batch2_file(path: str, text: str) -> dict[str, Any]:
    lower = path.lower()
    if lower.endswith("tsconfig.json"):
        kind = "tsconfig"
        parsed = parse_tsconfig(text)
    elif lower.endswith("pyproject.toml"):
        kind = "pyproject"
        parsed = parse_pyproject(text)
    elif lower.endswith("cargo.toml"):
        kind = "cargo"
        parsed = parse_cargo_toml(text)
    elif lower.endswith("pnpm-workspace.yaml"):
        kind = "pnpm_workspace"
        parsed = parse_pnpm_workspace(text)
    elif lower.endswith("turbo.json"):
        kind = "turbo"
        parsed = parse_turbo_json(text)
    elif lower.endswith("nx.json"):
        kind = "nx"
        parsed = parse_nx_json(text)
    else:
        kind = "linter"
        parsed = parse_linter_config(path, text)
    return {"kind": kind, "path": path, "parsed": parsed}


def _rule_count(data: Any) -> int:
    if not isinstance(data, dict):
        return 0
    rules = data.get("rules")
    if isinstance(rules, dict):
        return len(rules)
    linter = data.get("linter")
    if isinstance(linter, dict) and isinstance(linter.get("rules"), dict):
        return sum(len(value) for value in linter["rules"].values() if isinstance(value, dict))
    return 0
