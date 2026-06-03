"""Tests for Batch 2 configuration parsers."""

from src.config_parsers import (
    parse_batch2_file,
    parse_cargo_toml,
    parse_pyproject,
    parse_tsconfig,
)


def test_parse_tsconfig_jsonc_extracts_compiler_options() -> None:
    parsed = parse_tsconfig(
        """
        {
          // comment
          "extends": "./base.json",
          "compilerOptions": {
            "strict": true,
            "target": "ES2022",
            "moduleResolution": "Bundler",
          }
        }
        """
    )

    assert parsed["extends"] == "./base.json"
    assert parsed["strict"] is True
    assert parsed["target"] == "ES2022"
    assert parsed["module_resolution"] == "Bundler"


def test_parse_pyproject_extracts_backend_and_tools() -> None:
    parsed = parse_pyproject(
        """
        [build-system]
        build-backend = "hatchling.build"

        [project]
        name = "demo"
        requires-python = ">=3.12"

        [tool.ruff]
        line-length = 100
        """
    )

    assert parsed["project_name"] == "demo"
    assert parsed["build_backend"] == "hatchling.build"
    assert parsed["uses_ruff"] is True


def test_parse_cargo_detects_workspace() -> None:
    parsed = parse_cargo_toml(
        """
        [workspace]
        members = ["crates/a", "crates/b"]
        """
    )

    assert parsed["workspace"] is True
    assert parsed["workspace_members"] == 2


def test_parse_batch2_file_classifies_linter_config() -> None:
    parsed = parse_batch2_file(
        "biome.json",
        '{"linter": {"rules": {"style": {"useConst": "error"}}}}',
    )

    assert parsed["kind"] == "linter"
    assert parsed["parsed"]["rule_count"] == 1
