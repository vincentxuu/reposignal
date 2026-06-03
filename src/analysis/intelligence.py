"""Human-readable insights and recommendations."""

from typing import Any


def generate_insights(results: dict[str, Any]) -> list[dict[str, str]]:
    """Generate human-readable insights from analysis results."""
    insights: list[dict[str, str]] = []

    mpct = results["matrix_usage"]["percentage"]
    if mpct >= 70:
        insights.append({
            "key": "matrix_high",
            "icon": "rocket",
            "en": f"Matrix strategies are mainstream: {mpct}% of repos use them for multi-platform/multi-version testing. If you're not using matrix, you're likely missing coverage.",
            "zh": f"Matrix strategy 已成主流：{mpct}% 的 repo 使用它進行多平台／多版本測試。如果你還沒用，可能漏掉了重要的測試覆蓋。",
        })
    elif mpct >= 40:
        insights.append({
            "key": "matrix_moderate",
            "icon": "bar_chart",
            "en": f"Matrix adoption at {mpct}% — common but not universal. Consider it for projects targeting multiple OS or runtime versions.",
            "zh": f"Matrix 採用率 {mpct}%——常見但未普及。如果你的專案需要支援多個 OS 或 runtime 版本，值得考慮。",
        })

    ppct = results["permissions_usage"]["percentage"]
    if ppct < 50:
        insights.append({
            "key": "permissions_low",
            "icon": "warning",
            "en": f"Only {ppct}% of workflows set explicit permissions. This is a security gap — GitHub defaults to read-write. Setting `permissions:` reduces blast radius of compromised tokens.",
            "zh": f"只有 {ppct}% 的 workflow 設定了明確的 permissions。這是安全缺口——GitHub 預設為 read-write。設定 `permissions:` 可以降低 token 外洩時的影響範圍。",
        })
    else:
        insights.append({
            "key": "permissions_good",
            "icon": "shield",
            "en": f"{ppct}% of workflows set explicit permissions — the ecosystem is moving toward least-privilege CI. Good practice to follow.",
            "zh": f"{ppct}% 的 workflow 設定了明確的 permissions——生態系正在走向最小權限 CI。值得跟進的好實踐。",
        })

    ai_count = results["ai_review_adoption"]["count"]
    ai_pct = round(ai_count / results["total_repos"] * 100, 1) if results["total_repos"] else 0
    if ai_count > 0:
        insights.append({
            "key": "ai_review",
            "icon": "sparkles",
            "en": f"{ai_count} repos ({ai_pct}%) have AI code review workflows. Early adopters include {', '.join(results['ai_review_adoption']['repos'][:5])}. This is a fast-moving trend — expect rapid growth.",
            "zh": f"{ai_count} 個 repo（{ai_pct}%）已導入 AI 程式碼審查。早期採用者包括 {', '.join(results['ai_review_adoption']['repos'][:5])}。這是快速發展的趨勢——預期會快速增長。",
        })

    actions = results.get("popular_actions_categorized") or results.get("popular_actions", [])
    if actions:
        top10 = actions[:10]
        surprising = [a for a in top10 if not a["action"].startswith("actions/") and not a["action"].startswith("docker/")]
        if surprising:
            names = ", ".join(f'`{a["action"]}`' for a in surprising)
            insights.append({
                "key": "surprising_actions",
                "icon": "eyes",
                "en": f"Non-official actions in the top 10: {names}. These community actions are gaining significant traction across top repos.",
                "zh": f"非官方 action 進入前 10 名：{names}。這些社群 action 正在頂級 repo 中獲得顯著關注。",
            })

    sec_count = results.get("security_scan_adoption", {}).get("count", 0)
    if sec_count > 0:
        sec_pct = round(sec_count / results["total_repos"] * 100, 1)
        insights.append({
            "key": "security_scan",
            "icon": "lock",
            "en": f"{sec_count} repos ({sec_pct}%) run automated security scans in CI. Supply chain security is no longer optional for serious projects.",
            "zh": f"{sec_count} 個 repo（{sec_pct}%）在 CI 中執行自動化安全掃描。供應鏈安全對認真的專案來說不再是選配。",
        })

    return insights


def generate_recommendations(results: dict[str, Any]) -> list[dict[str, str]]:
    """Generate actionable recommendations based on analysis."""
    recs: list[dict[str, str]] = []

    mpct = results["matrix_usage"]["percentage"]
    if mpct >= 50:
        recs.append({
            "priority": "high",
            "en": f"**Add matrix testing** — {mpct}% of top repos test across multiple OS/versions. Start with `matrix: {{os: [ubuntu-latest, macos-latest], python: ['3.11', '3.12']}}`.",
            "zh": f"**加入 matrix 測試** — {mpct}% 的頂級 repo 會跨多個 OS/版本測試。從 `matrix: {{os: [ubuntu-latest, macos-latest], python: ['3.11', '3.12']}}` 開始。",
        })

    ppct = results["permissions_usage"]["percentage"]
    if ppct >= 30:
        recs.append({
            "priority": "high",
            "en": "**Set explicit `permissions:`** — Add `permissions: {contents: read}` to every workflow. It's the single easiest security hardening step.",
            "zh": "**設定明確的 `permissions:`** — 在每個 workflow 加入 `permissions: {contents: read}`。這是最簡單的安全強化步驟。",
        })

    cache_actions = [a for a in results.get("popular_actions", []) if "cache" in a["action"].lower()]
    if cache_actions:
        total_cache = sum(a["count"] for a in cache_actions)
        recs.append({
            "priority": "medium",
            "en": f"**Use caching** — Cache actions appear {total_cache} times across these repos. `actions/cache` or language-specific caches (e.g., `Swatinem/rust-cache`) can cut CI time by 30-60%.",
            "zh": f"**使用快取** — Cache action 在這些 repo 中出現 {total_cache} 次。`actions/cache` 或語言專用快取（如 `Swatinem/rust-cache`）可以減少 30-60% 的 CI 時間。",
        })

    ai_count = results["ai_review_adoption"]["count"]
    if ai_count > 0:
        recs.append({
            "priority": "medium",
            "en": f"**Try AI code review** — {ai_count} repos already use it. `anthropics/claude-code-action` is the most popular. Low effort to add, catches issues humans miss.",
            "zh": f"**試試 AI 程式碼審查** — 已有 {ai_count} 個 repo 在使用。`anthropics/claude-code-action` 最受歡迎。導入成本低，能抓到人工容易忽略的問題。",
        })

    return recs
