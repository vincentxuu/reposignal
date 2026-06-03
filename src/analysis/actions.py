"""GitHub Action categorization and AI review metadata."""

ACTION_CATEGORIES: dict[str, list[str]] = {
    "CI/Build": [
        "actions/checkout", "actions/setup-python", "actions/setup-node",
        "actions/setup-go", "actions/setup-java", "actions/setup-dotnet",
        "astral-sh/setup-uv", "pnpm/action-setup", "oven-sh/setup-bun",
    ],
    "Artifacts": [
        "actions/upload-artifact", "actions/download-artifact",
    ],
    "Cache/Performance": [
        "actions/cache", "actions/cache/restore", "actions/cache/save",
        "Swatinem/rust-cache",
    ],
    "Docker/Container": [
        "docker/login-action", "docker/setup-buildx-action",
        "docker/build-push-action", "docker/setup-qemu-action",
        "docker/metadata-action",
    ],
    "Security": [
        "aquasecurity/trivy-action", "github/codeql-action",
        "ossf/scorecard-action", "snyk/actions",
        "securego/gosec", "returntocorp/semgrep-action",
        "gitleaks/gitleaks-action",
    ],
    "AI Review": [
        "anthropics/claude-code-action", "github/copilot-code-review",
    ],
    "Automation": [
        "actions/github-script", "peter-evans/create-pull-request",
        "actions/create-github-app-token", "actions/stale",
    ],
    "Cloud/Deploy": [
        "azure/login", "aws-actions/configure-aws-credentials",
        "google-github-actions/auth",
    ],
}


AI_REVIEW_TOOLS: dict[str, dict[str, str]] = {
    "anthropics/claude-code-action": {
        "name": "Claude Code Action",
        "model": "Claude (Anthropic)",
        "approach": "Full codebase-aware review with multi-file context. Can run commands, write code, and create review comments.",
        "approach_zh": "具備完整程式碼庫感知的審查，支援多檔案上下文。可執行指令、撰寫程式碼、建立審查評論。",
        "prompt_style": "Configurable via `direct_prompt` or `review_prompt` inputs. Default: comprehensive PR review.",
        "prompt_style_zh": "可透過 `direct_prompt` 或 `review_prompt` 輸入自訂。預設：全面 PR 審查。",
    },
    "github/copilot-code-review": {
        "name": "GitHub Copilot Code Review",
        "model": "GPT-4 (GitHub/OpenAI)",
        "approach": "Integrated into GitHub's native review system. Adds inline suggestions as review comments.",
        "approach_zh": "整合進 GitHub 原生審查系統。以 inline 建議方式加入審查評論。",
        "prompt_style": "Not user-configurable. GitHub controls the review behavior.",
        "prompt_style_zh": "不可由使用者自訂。由 GitHub 控制審查行為。",
    },
    "coderabbitai/ai-pr-reviewer": {
        "name": "CodeRabbit AI PR Reviewer",
        "model": "GPT-4 (OpenAI)",
        "approach": "Automated PR summary + line-by-line review. Generates a walkthrough of changes.",
        "approach_zh": "自動 PR 摘要 + 逐行審查。產生變更的 walkthrough。",
        "prompt_style": "Configurable via `.coderabbit.yaml`. Supports custom review instructions and path filters.",
        "prompt_style_zh": "可透過 `.coderabbit.yaml` 設定。支援自訂審查指示和路徑過濾。",
    },
    "sourcery-ai/action": {
        "name": "Sourcery AI",
        "model": "Sourcery proprietary + GPT-4",
        "approach": "Focuses on code quality: refactoring suggestions, complexity reduction, best practices.",
        "approach_zh": "專注於程式碼品質：重構建議、降低複雜度、最佳實踐。",
        "prompt_style": "Configured via `.sourcery.yaml`. Rule-based + AI hybrid.",
        "prompt_style_zh": "透過 `.sourcery.yaml` 設定。規則式 + AI 混合模式。",
    },
}


def action_url(action: str) -> str:
    """Generate GitHub Marketplace or repo URL for an action."""
    parts = action.split("/")
    if len(parts) >= 2:
        return f"https://github.com/{'/'.join(parts[:2])}"
    return ""


def categorize_actions(
    popular_actions: list[dict],
    descriptions: dict[str, str] | None = None,
) -> list[dict]:
    """Assign a category, description, and URL to each popular action."""
    descriptions = descriptions or {}
    reverse: dict[str, str] = {}
    for category, patterns in ACTION_CATEGORIES.items():
        for pattern in patterns:
            reverse[pattern] = category

    result = []
    for entry in popular_actions:
        action = entry["action"]
        category = reverse.get(action)
        if not category:
            for pattern, candidate in reverse.items():
                if action.startswith(pattern):
                    category = candidate
                    break
        result.append({
            **entry,
            "category": category or "Other",
            "desc": descriptions.get(action, ""),
            "url": action_url(action),
        })
    return result
