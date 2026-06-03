# RepoSignal MVP

## Why

目前市場上有「找熱門 repo」的工具（OSSInsight、Trendshift）和「列好用 Actions」的清單（awesome-actions），但**沒有人自動跨專案爬取 workflow、分析 CI/CD pattern、歸納最佳實踐**。這是一個明確的市場空缺。

研究調查了 70+ 個頂級開源專案、涵蓋 20 個技術領域，辨識出 20 種 CI/CD 架構模式（AI-as-CI-agent、Chaos engineering、Ecosystem CI、Multi-stage release train 等），並提出 20 個產品方向。RepoSignal 已有可運作的核心管道（爬蟲→提取→分析→報告），能從 200 個開源專案爬取 3,128 個 workflow 並生成雙語分析報告。但目前：

- **分析維度有限**：僅覆蓋 workflow YAML，未涵蓋研究中發現的延伸面向（linter 配置、monorepo 結構、依賴管理、release 策略等 15 個觀察面向）
- **20 種 pattern 未結構化**：研究手動歸納的 pattern（AI-as-CI-agent、Dogfooding、Chaos engineering 等）尚未轉化為可自動偵測的分類邏輯
- **缺乏時間維度**：無差異追蹤、趨勢偵測、Workflow Changelog
- **無對外發佈機制**：報告只在本地生成，沒有自動化排程和靜態網站
- **產品功能為零**：研究提出的 Workflow Generator、Pattern Library、Security Dashboard 等均未開始

此 MVP 要將研究成果與現有原型升級為可持續運作、對外提供價值的完整產品。

## 目標受眾

開發者 — 寫 GitHub Actions 的人、技術主管、DevOps 實踐者。

## What Changes

### 現有能力盤點

```
已建成                              尚未建成
════════                            ════════
✅ GitHub API 爬蟲 (async, rate-limit)  ❌ Pattern 結構化偵測 (20 種)
✅ YAML → Parquet 提取器               ❌ 歷史快照 + 差異追蹤
✅ DuckDB 分析查詢                     ❌ 延伸面向爬蟲 (15 種檔案)
✅ Jinja2 雙語報告                     ❌ 安全評分系統
✅ Action enricher (description/AI)    ❌ 靜態網站
✅ 200 repos, 3,128 workflows          ❌ 任何對外發佈機制
✅ 基本分析：matrix/actions/AI/security ❌ CLI / API
                                       ❌ 正規 ETL 管道（schema/增量/品質監控）
```

### Seed Repos 管理

Seed list 是**版本化管理的核心清單**，可以增加、可以替換、可以移除，但每次變更都有紀錄。

最新狀態由 `seed_repos.json`（清單）和 `seed_repos_metadata.json`（GitHub API 同步的 metadata）為單一事實來源，`src/scripts/generate_overview.py` 可隨時產生語言分佈、分類統計等概覽報告（輸出至 `data/seeds/overview-*.md`）。

**目前覆蓋範圍**：200+ repos、20+ 種程式語言，以 Python、TypeScript、Go、Rust、JavaScript 為大宗。詳見最新的 `seed_repos_overview.md`。

**現況問題：每次重建可能產出不同的 200 個 repo**

目前 `build_seed_list.py` 每次執行都從 research markdown + GitHub Search API（`stars:>5000`）重新組合清單。新 repo 衝上 stars 門檻、舊 repo 被 archive、workflow 數量變化都會改變結果。這對趨勢分析是致命缺陷——「matrix 採用率從 45% → 52%」到底是趨勢變了，還是 repo 名單換了？無法區分。

**改進：版本化 Seed List**

核心原則：**清單可以變，但要有紀錄，且分析時要控制變因。**

```
seed_repos.json（v1: 初始 200 個，commit 進 repo）
     │
     ├── v1.1: +5 repos（補齊 Kotlin 領域）、-2 repos（archived）
     ├── v1.2: +10 repos（Spring ecosystem）
     ├── v2.0: 擴充至 300+（Phase 2）
     └── ...
```

| 規則 | 說明 |
|---|---|
| **變更即 commit** | 每次增減都是一筆 git commit，寫清楚「加了誰、移了誰、為什麼」 |
| **crawl 綁定版本** | 每次 crawl 記錄「本次用的是哪個版本的 seed list」，分析結果可追溯到確切的 repo 集合 |
| **趨勢用交集比較** | 比較兩次 crawl 的趨勢時，只取**兩次都存在的 repo 交集**，排除因名單變動造成的假趨勢 |
| **`build_seed_list.py` 改為候選產生器** | 腳本輸出作為「候選名單」供人工審核，不再直接覆蓋核心清單 |

**什麼時候該變更 Seed List？**

| 情境 | 動作 |
|---|---|
| repo 被 archive / 刪除 | 移除，commit 標記原因 |
| repo 不再維護（2 年沒 push） | 移除，commit 標記原因 |
| 發現更好的同領域代表 | 替換，commit 標記原因 |
| 補齊新語言 / 新領域 | 新增，不需移除既有的 |
| Phase 2 擴充 | 有計畫地擴充至 300+，補齊 Java/C#/Ruby/Kotlin 等傳統領域標竿專案 |
| 自助健檢上線後 | 使用者提交的 repo 若符合條件可納入。納入標準不設固定門檻，由當時的覆蓋缺口決定（缺某語言 → 降門檻；飽和 → 提高門檻或不收）。唯一硬性條件：repo 必須有至少一個 GitHub Actions workflow |

### ETL 管道正規化

**什麼是 ETL？**

ETL（Extract → Transform → Load）是資料工程的核心模式：從來源「抽取」原始資料、「轉換」成結構化格式、「載入」到可供查詢的儲存層。RepoSignal 的現有管道其實已經是 ETL，只是缺乏正規 ETL 的關鍵特性。

**現有管道 vs 正規 ETL — 以 RepoSignal 為例**

```
現有管道                    正規 ETL 對應          缺口
════════                   ════════════          ════
crawler.py (GitHub API)  → Extract               無增量爬取
extractors/cicd.py       → Transform (parse)     無 schema 驗證
analyzer.py (DuckDB)     → Transform (aggregate) 無品質監控
reporter.py (Jinja2)     → 下游消費者             無血緣追蹤
run.py                   → Orchestration         寫死順序，無 DAG
```

以下用 RepoSignal 的實際管道逐一說明每個 ETL 正規概念：

---

**1. Schema Validation（資料契約）— Phase 0**

> 問題：`crawler.py` 抓回的 raw YAML 交給 `extractors/cicd.py` 解析，但兩者之間沒有明確約定「交出的資料長什麼樣」。如果 GitHub API 回傳格式變了、或解析邏輯漏掉欄位，下游 `analyzer.py` 會默默產出錯誤結果。

用 Pydantic model 定義「Extract 交給 Transform 的資料契約」：

```python
# 現況：extractor 直接 append dict，欄位靠人腦記
rows.append({
    "repo": "facebook/react",
    "workflow": "ci.yml",
    "actions_normalized": ["actions/checkout", "actions/setup-node"],
    "has_matrix": True,
    "permissions": {"contents": "read"},
    ...
})

# 正規化後：Pydantic model 作為契約，欄位缺失或型別錯會立即報錯
class WorkflowRecord(BaseModel):
    repo: str
    workflow: str
    actions_normalized: list[str]
    has_matrix: bool
    permissions: dict[str, str] | None
    security_tools: list[str]
    crawl_date: date
```

好處：crawler 改了、GitHub API 改了、extractor 改了，只要不符合契約就會在管道最早的階段報錯，而不是等到報告出來才發現數字怪怪的。

---

**2. Idempotency（增量爬取）— Phase 0**

> 問題：現在 `crawler.py` 每次都重新爬取全部 200 個 repo 的所有 workflow 檔案（~3,128 個），即使大部分 repo 自上次爬取後沒有任何變更。浪費 GitHub API quota，也拖慢管道速度。

HTTP 協議本身就有增量機制：

```python
# 現況：每次無條件爬取
response = await client.get(f"/repos/{repo}/contents/.github/workflows")

# 正規化後：用 ETag / Last-Modified 做增量
# 第一次爬取時，GitHub 回傳 ETag header，存到本地
# 之後帶上 If-None-Match，若檔案沒變 GitHub 回 304 Not Modified（不計入 rate limit）
headers = {"If-None-Match": cached_etag}
response = await client.get(url, headers=headers)
if response.status_code == 304:
    # 檔案沒變，跳過，省下 API quota
    continue
```

效果：假設每週只有 20% 的 repo 更新 workflow，管道速度提升 5 倍、API 呼叫量降至 1/5。

---

**3. Partitioning（分區儲存）— Phase 0**

> 問題：現在只有一個 `data/processed/cicd.parquet`，每次跑管道就整個覆蓋。無法回答「上個月 React 的 workflow 長什麼樣？」、無法比較兩次 crawl 的差異。

按 crawl_date 分區：

```
# 現況：單一檔案，每次覆蓋
data/processed/cicd.parquet

# 正規化後：按日期分區，歷史永遠保留
data/processed/
├── crawl_date=2026-03-22/cicd.parquet   ← 上週的快照
├── crawl_date=2026-03-29/cicd.parquet   ← 這週的快照
└── crawl_date=2026-04-05/cicd.parquet   ← 下週的快照
```

DuckDB 可以直接查詢分區目錄：`SELECT * FROM 'data/processed/*/cicd.parquet' WHERE crawl_date = '2026-03-29'`。這也是 Phase 1 Workflow Changelog 的基礎——比較兩個日期的 parquet 就能找出差異。

---

**4. DAG Orchestration（管道編排）— Phase 1**

> 問題：現在 `run.py` 是寫死的 Step 1→2→3→4→5→6 順序。如果 Step 3 失敗，要整條管道從頭跑。也無法只重跑某一步、無法監控每步的狀態。

Dagster 用 **software-defined assets**（資料資產）取代傳統的「task 順序」：

```python
# 現況 run.py：寫死順序，一步壞全部重來
stats = await crawl(seed_file)          # Step 1
ai_actions = await discover_ai_review_actions()  # Step 2
df = extractor.extract(raw_dir)          # Step 3
results = analyze(action_descriptions)    # Step 5
report = generate_report(results)         # Step 6

# Dagster：定義「資料資產」之間的依賴關係
@asset
def raw_workflows():
    """Extract: 從 GitHub 爬取 workflow YAML"""
    return crawl(seed_file)

@asset(deps=[raw_workflows])
def cicd_parquet(raw_workflows):
    """Transform: YAML → 結構化 Parquet"""
    return extractor.extract(raw_dir)

@asset(deps=[cicd_parquet])
def analysis_json(cicd_parquet):
    """Transform: Parquet → 分析結果 JSON"""
    return analyze()

@asset(deps=[analysis_json])
def report_md(analysis_json):
    """Load: 分析結果 → Markdown 報告"""
    return generate_report(analysis_json)
```

好處：
- Dagit UI 可視化看到 `raw_workflows → cicd_parquet → analysis_json → report_md` 的 DAG 圖
- `cicd_parquet` 失敗了？只重跑這一步，不需從 crawl 重來
- 每個 asset 有執行狀態、耗時、產出 metadata
- Phase 2 新增 15 個面向時，每個面向就是一個獨立 asset，可平行執行

---

**5. Data Validation（品質驗證）— Phase 1**

> 問題：`extractor` 產出的 DataFrame 可能有 null 值、重複行、schema 漂移（某次 GitHub API 變更導致欄位消失），但目前完全沒有檢查。

在每個 asset 產出後驗證品質：

```python
# 用 Pandera 定義 DataFrame 的品質規則
import pandera.polars as pa

class CICDSchema(pa.DataFrameModel):
    repo: str = pa.Field(nullable=False)        # repo 不能為 null
    workflow: str = pa.Field(nullable=False)     # workflow 名稱不能為 null
    has_matrix: bool                             # 必須是布林值
    actions_normalized: list[str]                # 必須是字串清單

    @pa.check("repo")
    def no_duplicates(cls, series):
        """同一 repo + workflow 不應重複"""
        return series.is_unique()
```

每次管道跑完，自動產出品質摘要：
- 總行數（這次 3,128 vs 上次 3,120 — 正常增長？還是 8 個 workflow 被刪了？）
- null rate（`permissions` 欄位 null 率從 15% 變 45% — GitHub API 出問題了？）
- schema drift（新增了未預期的欄位？少了預期的欄位？）

---

**6. Run Metadata（執行元數據）— Phase 1**

每次管道執行自動記錄：

```json
{
  "run_id": "2026-03-29T08:30:00Z",
  "steps": {
    "crawl": { "duration_sec": 142, "repos": 200, "files": 3128, "errors": 3 },
    "extract": { "duration_sec": 8, "rows": 3128, "null_rate": {"permissions": 0.15} },
    "analyze": { "duration_sec": 12, "output_size_kb": 340 },
    "report": { "duration_sec": 2, "pages": ["en", "zh-tw"] }
  }
}
```

這讓你可以追蹤：管道是不是越跑越慢？錯誤率是不是在上升？哪個步驟是瓶頸？

---

**7. Multi-asset Pipeline（多資產管道）— Phase 2**

Phase 2 新增 15 個觀察面向（linter 配置、monorepo 結構、release 策略等），每個面向是獨立的 Dagster asset：

```
                    raw_workflows ──→ cicd_parquet ──→ pattern_detection
                   /                                    ──→ security_score
  crawl_asset ────                                      ──→ changelog
                   \
                    raw_configs ────→ linter_parquet ──→ config_trends
                   /
                    raw_codeowners → community_health
                    raw_release ───→ release_strategy
                    ...（15 個面向）
```

每個面向可以獨立跑、獨立失敗、獨立重試。新增一個面向 = 新增一個 asset，不影響其他面向。

---

**8. Lineage Tracking（血緣追蹤）— Phase 2**

> 問題：報告說「React 的安全評分是 85 分」，但這個 85 分是從哪些 workflow 檔案算出來的？如果結果有疑問，怎麼追溯到原始資料？

```
報告：「facebook/react security_score = 85」
  ↑ 來自 analysis_json["security"]["facebook/react"]
    ↑ 來自 cicd_parquet WHERE repo = 'facebook/react'
      ↑ 來自 raw files:
        - data/raw/facebook/react/ci.yml（crawl_date=2026-03-29）
        - data/raw/facebook/react/runtime_build.yml
        - data/raw/facebook/react/devtools.yml
```

每筆分析結果附帶 `source_files` 欄位，讓任何數字都能一路追溯到原始 YAML。

---

**9. Data Quality Dashboard（品質儀表板）— Phase 2**

把上述所有品質指標集中呈現，跟分析報告一起產出：

```
📊 資料品質摘要 — 2026-03-29
━━━━━━━━━━━━━━━━━━━━━━━━━━
覆蓋率：200 repos, 169 有 workflow (84.5%)
完整度：permissions 欄位 85% 非 null ✅
        security_tools 欄位 72% 非 null ⚠️ (低於閾值 80%)
新鮮度：最舊的 raw file 來自 3 天前 ✅
異常值：ollama/ollama workflow 數從 4 → 47 🚨 需人工確認
Schema：無 drift ✅
```

---

**為什麼選 Dagster？**

| 考量 | Dagster | Airflow | Prefect |
|---|---|---|---|
| 核心概念 | **Software-defined assets**（資料資產導向） | Task DAG（任務導向） | Flow/Task（任務導向） |
| 適合 RepoSignal 的理由 | 每個 parquet/json 就是一個 asset，天然對應 | 需要自己管理檔案狀態 | 需要自己管理檔案狀態 |
| 內建 UI | Dagit — 可看 asset 依賴圖、執行狀態、品質指標 | Airflow UI — 功能強但偏重排程 | Prefect UI — 需要 Cloud 版才完整 |
| 學習曲線 | 中等（概念新但 API 直覺） | 高（配置複雜、Executor 選擇多） | 低（但 asset 概念弱） |
| Python-native | 是 | 是 | 是 |
| 部署 | 本地開發直接 `dagster dev`，生產可用 Docker | 需要 scheduler + webserver + worker | 需要 agent + API server |

### Pattern 分類體系：20 種 → 7 大類

研究歸納的 20 種 CI/CD pattern 重新整理為 7 大類，按偵測難度分三個 Tier：

**7 大類**

| 大類 | 子 Pattern | 數量 |
|---|---|---|
| AI-Powered CI | AI code review, AI security review, AI 貢獻審計, Dogfooding | 4 |
| Security & Supply Chain | Security scanning, Container 簽署, Harden runner, Permissions 最小化 | 4 |
| Testing Strategy | 多硬體平台矩陣, Chaos engineering, Fuzz/randomized, Flaky test retry, Performance tracking, Python 前瞻測試 | 6 |
| Release Pipeline | Multi-stage release, 多通道發佈, PR 即套件預覽 | 3 |
| Workflow Architecture | Reusable workflows, 多 build system, 每 sample 各自 CI | 3 |
| Ecosystem Integration | Ecosystem CI (跨 repo 觸發) | 1 |
| Cross-version Compat | 多版本矩陣 | 1 |

**3 個偵測 Tier**

| Tier | 偵測方式 | Pattern 數 | 階段 |
|---|---|---|---|
| Tier 1 | Action 名稱 / 關鍵字比對 | 14 | Phase 1 前半 |
| Tier 2 | YAML 結構分析 | 6 | Phase 1 後半 |
| Tier 3 | 跨 workflow 推理 | 2 | Phase 2 |

**Tier 1 — Action/關鍵字比對（14 種）**

| Pattern | 偵測方式 |
|---|---|
| AI code review | 比對已知 AI action 清單（已有） |
| AI security review | AI action + security 關鍵字 |
| AI 貢獻審計 | check-ai-coauthors action |
| Security scanning | trivy/codeql/gitleaks...（已有） |
| Container 簽署 | cosign/sigstore/syft |
| Harden runner | step-security/harden-runner |
| Permissions 最小化 | permissions: 欄位存在（已有） |
| Chaos engineering | chaos-mesh/litmus/toxiproxy |
| Fuzz / randomized | fuzz/property-based 關鍵字 |
| Performance tracking | benchmark/callgrind/valgrind |
| PR 即套件預覽 | pkg.pr.new |
| Reusable workflows | uses: ./.github/workflows/ |
| Python 前瞻測試 | matrix 含 3.14/free-threaded |
| Cross-version compat | matrix dimension ≥ 3 versions |

**Tier 2 — YAML 結構分析（6 種）**

| Pattern | 偵測方式 |
|---|---|
| 多硬體平台矩陣 | 解析 matrix 值，分類為 OS/arch/hardware |
| Flaky test retry | 偵測 retry 邏輯（step retry/dedicated workflow） |
| 多通道發佈 | 分析 workflow 名稱 + trigger 條件 |
| 多 build system | 偵測同一 repo 有 Nix + Make + Bazel 等 |
| 每 sample 各自 CI | workflow 數量/命名異常模式 |
| Dogfooding | workflow 引用同 org 的 action |

**Tier 3 — 跨 workflow 推理（2 種）**

| Pattern | 偵測方式 |
|---|---|
| Multi-stage release | 多個 release workflow 之間的依賴關係 |
| Ecosystem CI | workflow_dispatch 的來源分析 |

### Repo 介紹（Repo Profile）

每個被追蹤的 repo 產生一份結構化介紹頁，讓讀者在深入 CI/CD 分析前先了解專案背景。

**資料來源與內容**

| 區塊 | 資料來源 | 說明 |
|---|---|---|
| 基本資訊 | GitHub API（已有） | description、stars、forks、language、license、topics、pushed_at |
| README 摘要 | GitHub API 抓取 README.md | 用 LLM 產生 2-3 句摘要，說明「這個專案做什麼、解決什麼問題」 |
| 技術棧概覽 | `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod` 等 | 主要依賴、框架、build tool |
| 社群健康度 | GitHub API Community Profile endpoint | CONTRIBUTING、CODE_OF_CONDUCT、ISSUE_TEMPLATE、PR_TEMPLATE 的有無 |
| CI/CD 摘要 | 現有分析結果 | workflow 數量、偵測到的 pattern 標籤、安全評分（Phase 1 後） |

**產出格式**

```
data/profiles/
├── ollama--ollama.json
├── facebook--react.json
└── ...
```

每個 JSON 含結構化欄位，供報告模板和網站 repo 頁面共用。

**引入時機**

| Phase | 做什麼 |
|---|---|
| Phase 0 | 基本資訊 profile（從已有 metadata 整理） + README 摘要（LLM） |
| Phase 1 | 加入 CI/CD 摘要（pattern 標籤 + 安全評分） |
| Phase 2 | 加入技術棧概覽 + 社群健康度（隨延伸爬蟲一起上線） |
| Phase 3 | 網站 `/repos/[owner]/[name]` 頁面，作為每個 repo 的入口 |

### 安全評分系統

```
Security Score = Σ(dimension × weight)

維度                    權重    計算方式
────────────────────────────────────────
permissions 顯式設定率   25%    workflow 有 permissions: 的比例
Security scan 覆蓋率    25%    偵測到的安全工具數 / 6（以 goreleaser 為基準）
Supply chain 工具       20%    SBOM + 簽署 + dependency review
Secret 處理            15%    是否用 GitHub App Token 而非 PAT
Harden runner          15%    是否使用 step-security/harden-runner

輸出：每 repo 0-100 分 + 排行榜 + 改善建議
```

### 延伸面向爬蟲（15 個面向，分 3 批）

**Batch 1 — 高價值、低複雜度（檔案存在即可偵測）**
- `.pre-commit-config.yaml`
- `CODEOWNERS`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `.github/dependabot.yml` / `renovate.json`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`

**Batch 2 — 需要解析內容**
- `tsconfig.json` / `pyproject.toml` / `Cargo.toml`（設定趨勢）
- `turbo.json` / `nx.json` / `pnpm-workspace.yaml`（monorepo）
- `.eslintrc` / `ruff.toml` / `biome.json`（linter 配置）

**Batch 3 — 需要較多邏輯**
- `.changeset/` / `.release-please-manifest.json` / `goreleaser.yml`（release 策略）
- `.devcontainer/` / `flake.nix` / `docker-compose.yml`（開發環境）
- `docs/rfcs/` / `docs/adr/`（技術決策記錄）

### 自助 Repo 健檢（Repo Health Check）

使用者在網站上貼上任意公開 GitHub repo 網址，系統即時爬取該 repo 的 workflow 和相關檔案，產生一份健檢報告。這是將 RepoSignal 的分析能力開放給所有人的殺手級功能。

**流程**

```
使用者輸入 repo URL
        │
        ▼
Pages Functions (Workers runtime) 接收請求
        │
        ▼
即時爬取（GitHub API）
├── .github/workflows/*.yml
├── 延伸面向檔案（CODEOWNERS、SECURITY.md 等）
└── repo metadata
        │
        ▼
即時分析（復用現有分析邏輯）
├── Pattern 偵測（7 大類 20 種）
├── 安全評分（0-100）
└── 與 seed repos 的百分位比較
        │
        ▼
產出健檢報告
├── 你的 repo 採用了哪些 CI/CD pattern
├── 安全評分 + 各維度細節
├── 「你的 repo vs 同語言 Top 50 repo 平均」
├── 具體改善建議（可複製的 YAML 片段）
└── 可分享的報告 URL
```

**技術考量**

| 面向 | 方案 |
|---|---|
| 速度 | GitHub API 爬取 + 分析控制在 10 秒內，前端 streaming 顯示進度 |
| Rate limit | 用 Cloudflare KV 快取分析結果（TTL 24h），避免重複爬取 |
| 濫用防護 | 每 IP 每小時上限 10 次（Cloudflare Rate Limiting） |
| 分析邏輯復用 | Python 分析邏輯編譯為 WASM 或改寫為 TypeScript 版，運行在 Pages Functions 上 |

**引入時機**：Phase 4（依賴 Phase 1 的 pattern 偵測 + 安全評分 + Phase 3 的網站基礎）

### 對外發佈：SvelteKit + Cloudflare（Pages + Workers）

使用 `@sveltejs/adapter-cloudflare` 部署至 **Cloudflare Pages**：prerendered 頁面（`prerender = true`）走 Pages CDN（零成本、無冷啟動），server routes 自動成為 **Pages Functions**（底層為 Workers runtime，透過 `platform.env` 存取 D1/KV/R2 bindings），**同一個 Pages 專案，不需分開管理 Pages 和 Workers**。圖表視覺化使用 **LayerCake**（Svelte 原生圖表庫）+ 需要時搭配 D3。

```
Python 管道（Dagster）             SvelteKit hybrid site
═══════════════════               ══════════════════

crawl → extract → analyze          Prerendered (CDN)
            │                      ├── /repos/[owner]/[name]
            ▼                      ├── /patterns/[slug]
    data/analysis/                 ├── /security/
    ├── current.json        ──▶    ├── /trends/
    ├── profiles.json              ├── /reports/
    ├── patterns.json              │
    ├── security.json              Pages Functions (Workers runtime)
    └── trends.json                ├── /api/patterns?lang=python
            │                      ├── /api/diff?a=vue&b=react
            ▼                      ├── /api/security/:repo
    reports/*.md            ──▶    └── /search?q=chaos
                                        │
                                   platform.env Bindings
                                   ├── D1  → 結構化查詢 (SQLite)
                                   ├── KV  → 快取層
                                   └── R2  → 大型 JSON 儲存

GitHub Actions:
  Python crawl → commit JSON → upload D1 → SvelteKit build → Cloudflare deploy
```

Phase 3 先做 prerendered pages（Pattern Library + Dashboard + Reports），Phase 4 加 Pages Functions server routes（API + Diff Tool + Search + 自助健檢），**同一個 SvelteKit + Cloudflare Pages 專案，不需另建後端**。

## 分階段規劃

核心原則：**每個 Phase 結束都有可發佈的產出物**。

### Phase 0 — 穩固基礎（重構 + 測試 + ETL 基礎）

鞏固既有程式碼，引入 ETL 正規化基礎，為後續擴充做準備。

| 項目 | 說明 |
|---|---|
| 拆分 analyzer | `analyzer.py` (31KB) → `analysis/matrix.py`, `analysis/actions.py`, `analysis/security.py`, `analysis/insights.py` |
| 測試補齊 | 現有管道的單元測試 + 整合測試 |
| Extractor 抽象化 | 強化 `extractors/base.py` 為可插拔介面，為 Phase 2 多面向爬蟲準備 |
| Pydantic schema | 為 crawler → extractor → analyzer 之間定義 Pydantic models 作為資料契約 |
| 增量爬取 | crawler 支援 ETag / Last-Modified，只抓新/變更的檔案 |
| Parquet 分區 | 按 crawl_date 分區，支援歷史查詢與增量更新 |
| Seed list 管理 | 有版本追蹤的管理方式 |
| Error handling | 結構化錯誤分類 |
| `repo-profile-v1` | 從已有 metadata 整理基本資訊 profile + LLM 產生 README 摘要（2-3 句），產出 `data/profiles/*.json` |

**產出**：同樣的報告，但程式碼結構乾淨、有 schema 契約、支援增量爬取、有測試、可安全擴充。每個 repo 有結構化介紹 profile。

### Phase 1 — Pattern 偵測引擎 + 安全評分 + Changelog v1 + Dagster

核心價值建立。報告從「統計」升級為「洞察」。同步引入 Dagster 作為管道編排引擎。

| Capability | 說明 |
|---|---|
| `pattern-detection` | Tier 1（14 種 action/關鍵字比對）+ Tier 2（6 種 YAML 結構分析），共 20 種 pattern 自動偵測，歸為 7 大類 |
| `security-posture` | 5 維度安全評分（0-100），排行榜 + 改善建議 |
| `repo-profile-v2` | Repo profile 加入 CI/CD 摘要（偵測到的 pattern 標籤 + 安全評分） |
| `workflow-changelog-v1` | 比較兩次 crawl 的差異：新增/刪除/修改的 workflow + 新出現的 pattern |
| `dagster-pipeline` | 用 Dagster software-defined assets 重寫管道編排：crawl_asset → extract_asset → analyze_asset → report_asset，可透過 Dagit UI 監控執行、重跑單步 |
| `data-validation` | 每個 asset 產出時驗證 schema 與品質指標（行數、null rate、schema drift） |

**產出**：報告新增「CI/CD Pattern 分類」（7 大類 20 種 pattern 採用率 + 範例）、「Security Posture 排行榜」（Top/Bottom 10）、「Workflow 變更摘要」。管道可透過 Dagit UI 監控。

### Phase 2 — 擴充資料維度 + 跨 repo 推理 + ETL 成熟化

從「只看 workflow」擴展到「看整個 repo 的工程實踐」。同步擴充 seed repos 語言多樣性。

| Capability | 說明 |
|---|---|
| `extended-crawler` | 分 3 批上線 15 個延伸觀察面向（Batch 1 檔案偵測 → Batch 2 內容解析 → Batch 3 結構推理） |
| `pattern-detection-tier3` | 補齊 Tier 3 的 2 種跨 workflow 推理 pattern（Multi-stage release、Ecosystem CI） |
| `config-trends` | 跨專案追蹤設定檔選項趨勢（tsconfig strict 採用率、pyproject build-backend 變遷等） |
| `workflow-diff-engine` | 兩個 repo 的結構化 CI 策略比較資料層 |
| `multi-asset-pipeline` | 15 個面向 = 15 個 Dagster asset，各自獨立 extract/transform，可平行執行 |
| `lineage-tracking` | 每筆分析結果可追溯到來源 raw file |
| `data-quality-dashboard` | 品質指標（完整度、異常值、schema drift）跟分析報告一起產出 |
| `seed-expansion` | 擴充 seed repos 至 300+，補齊 Go/Rust/Java/C#/Ruby 等傳統領域標竿專案 |
| `repo-profile-v3` | Repo profile 加入技術棧概覽 + 社群健康度（隨延伸爬蟲一起上線） |

**產出**：報告新增「工程實踐全景」（15 面向採用率）、「設定檔趨勢」、「資料品質摘要」，CLI 支援 `--diff repo-a repo-b`。

### Phase 3 — SvelteKit 網站 + Cloudflare Pages 部署

把累積的資料和分析變成可公開訪問的產品。

| Capability | 說明 |
|---|---|
| `pattern-library` | 互動式 pattern 目錄：7 大類 × 20 種 pattern，每個 pattern 含真實範例、可複製 YAML、採用率、趨勢 |
| `repo-profile-page` | 每個 repo 的介紹頁 `/repos/[owner]/[name]`：基本資訊 + README 摘要 + 技術棧 + CI/CD pattern 標籤 + 安全評分，作為 repo 入口頁 |
| `security-dashboard` | Security Posture 排行榜 + 單 repo 評分詳情 |
| `trends-page` | 設定檔趨勢圖表 + 歷史比較 |
| `benchmark-report` | 月度/季度自動發佈 CI/CD Benchmark Report |
| `scheduled-pipeline` | GitHub Actions 自動化排程（每週 crawl → analyze → build → deploy） |
| `static-site` | SvelteKit 靜態網站部署至 Cloudflare Pages |

**產出**：可公開訪問的網站（Pattern Library + Security Dashboard + Trends），每週自動更新，月度 Benchmark Report。

### Phase 4 — 進階工具（長期）

| Capability | 說明 |
|---|---|
| `workflow-generator` | 輸入技術棧 → 從真實 pattern 組合最佳 workflow |
| `workflow-diff-ui` | 選兩個 repo 並排比較 CI 策略（網頁版） |
| `ci-copilot` | AI 建議該加什麼 workflow |
| `workflow-migrator` | 跨 CI 平台轉換 |
| `flaky-test-detective` | 跨 repo 收集 flaky test pattern |
| `ai-pr-reviewer-kit` | 一鍵加 AI code review |
| `json-api` | SvelteKit server routes + D1，提供 pattern 查詢、repo 比較、安全評分的程式化存取（同一個 SvelteKit 專案，不需另建後端） |
| `repo-health-check` | 貼上任意公開 repo 網址，即時爬取並產生健檢報告（CI/CD pattern 偵測 + 安全評分 + 改善建議），不限於 seed repos |

**產出**：開發者可互動使用的工具 + API + 自助健檢。

## Capabilities

### New Capabilities

**Phase 0 — 穩固基礎 + ETL 基礎**

- `refactored-analysis`: 拆分 analyzer.py 為模組化分析引擎，可插拔 extractor 介面
- `test-coverage`: 現有管道的單元測試 + 整合測試覆蓋
- `pydantic-schema`: 管道各層之間的 Pydantic models 資料契約
- `incremental-crawl`: 支援 ETag/Last-Modified 的增量爬取
- `partitioned-storage`: Parquet 按 crawl_date 分區
- `repo-profile-v1`: 從已有 metadata 整理基本資訊 profile + LLM 產生 README 摘要，產出 `data/profiles/*.json`

**Phase 1 — Pattern 引擎 + 安全評分 + Dagster**

- `repo-profile-v2`: Repo profile 加入 CI/CD 摘要（偵測到的 pattern 標籤 + 安全評分）
- `pattern-detection`: 7 大類 20 種 CI/CD pattern 自動偵測（Tier 1 + Tier 2），含採用率統計與範例連結
- `security-posture`: 5 維度安全評分（0-100），排行榜 + 改善建議
- `workflow-changelog-v1`: 兩次 crawl 差異比較，偵測新增/刪除/修改的 workflow 與新出現的 pattern
- `dagster-pipeline`: Dagster software-defined assets 管道編排 + Dagit UI 監控
- `data-validation`: 每個 asset 產出時的 schema 與品質驗證

**Phase 2 — 擴充資料維度 + ETL 成熟化**

- `extended-crawler`: 15 個延伸觀察面向的爬蟲（分 3 批上線）
- `pattern-detection-tier3`: 2 種跨 workflow 推理 pattern（Multi-stage release、Ecosystem CI）
- `config-trends`: 跨專案設定檔選項趨勢追蹤
- `workflow-diff-engine`: 兩個 repo 的結構化 CI 策略比較
- `multi-asset-pipeline`: 15 個面向各自獨立 Dagster asset，可平行執行
- `lineage-tracking`: 分析結果到來源 raw file 的血緣追蹤
- `data-quality-dashboard`: 資料品質指標監控
- `seed-expansion`: 擴充 seed repos 至 300+，補齊語言多樣性
- `repo-profile-v3`: Repo profile 加入技術棧概覽 + 社群健康度

**Phase 3 — 對外發佈**

- `repo-profile-page`: 每個 repo 的介紹頁 `/repos/[owner]/[name]`（SvelteKit 頁面）
- `pattern-library`: 互動式 CI/CD pattern 目錄（SvelteKit 頁面）
- `security-dashboard`: Security Posture 排行榜 + 詳情頁
- `trends-page`: 設定檔趨勢圖表
- `benchmark-report`: 月度/季度 CI/CD Benchmark Report
- `scheduled-pipeline`: GitHub Actions 自動化排程
- `static-site`: SvelteKit + Cloudflare Pages 部署

**Phase 4 — 進階工具**

- `workflow-generator`: 技術棧 → 最佳 workflow 範本
- `workflow-diff-ui`: 網頁版 repo CI 策略比較
- `ci-copilot`: AI 驅動 CI 配置建議
- `workflow-migrator`: 跨 CI 平台轉換
- `flaky-test-detective`: Flaky test pattern 分析
- `ai-pr-reviewer-kit`: 一鍵 AI code review 設定
- `json-api`: SvelteKit server routes + Cloudflare D1 API（同一專案內，不需另建後端）
- `repo-health-check`: 貼上公開 repo 網址即時健檢（pattern 偵測 + 安全評分 + 改善建議 + 百分位比較）

### Modified Capabilities

（目前 `openspec/specs/` 為空，無既有 capability 需修改）

## Impact

- **程式碼**：Phase 0 重構 `src/analyzer.py` → `src/analysis/` + 新增 Pydantic schemas；Phase 1 新增 `src/patterns.py`、`src/security.py`、`src/changelog.py` + Dagster definitions；Phase 2 新增 `src/extractors/` 多個面向提取器、`src/diff.py`、`src/trends.py`；Phase 3 新增 `site/` (SvelteKit 專案)
- **資料**：`data/` 新增 `profiles/`（repo 介紹 JSON）、`snapshots/`（歷史快照）、`changelog/`（變更記錄）、`configs/`（設定檔快照），Parquet 改為按 crawl_date 分區
- **依賴**：Python 側新增 `dagster`（管道編排）、`pydantic`（schema）、`pandera`（DataFrame 驗證）、可能新增 `click`（CLI）；Phase 3 新增 Node.js 依賴（SvelteKit + LayerCake + Tailwind）
- **API**：GitHub API 呼叫量因擴充爬蟲範圍增加，Phase 0 引入增量爬取（ETag/Last-Modified）管理 rate limit
- **基礎設施**：Phase 1 新增 Dagit UI（本地開發監控）；Phase 3 新增 `.github/workflows/` 自動化管道 + Cloudflare Pages 部署
- **資料量**：Phase 2 從 200 repos 擴至 300+、從 workflow-only 擴至 15 個觀察面向，預估資料量成長 5-10 倍

## 總覽

```
Phase   焦點                          ETL 進度              Pattern        Repo Profile     主要產出
─────   ────                          ────────              ───────        ────────────     ────────
  0     重構 + 測試 + ETL 基礎         Pydantic + 增量 + 分區  —              基本資訊+README摘要 乾淨架構、可擴充
  1     Pattern 引擎 + 安全評分        Dagster + 品質驗證      Tier 1+2 (20)  +CI/CD摘要+評分   7 大類 pattern + 安全排行
  2     擴充資料 + 跨 repo 推理        多 asset + 血緣 + 品質   + Tier 3 (2)   +技術棧+社群健康  15 面向 + 趨勢 + 300 repos
  3     SvelteKit 網站 + CF 部署       排程自動化              —              網站 repo 頁面    Pattern Library + Dashboard
  4     進階工具 + Workers API         —                      —              +自助健檢         Generator / Diff / API
```
