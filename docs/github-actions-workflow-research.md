# GitHub Actions Workflow 開源專案研究

> 調查時間：2026-03-29
> 總計收錄：70+ 個專案

---

## 目錄

1. [LLM 推論引擎](#1-llm-推論引擎)
2. [AI Agent 框架](#2-ai-agent-框架)
3. [RAG / 向量資料庫](#3-rag--向量資料庫)
4. [訓練 / 微調](#4-訓練--微調)
5. [AI Coding 工具](#5-ai-coding-工具)
6. [Multimodal / Diffusion](#6-multimodal--diffusion)
7. [AI 基礎設施](#7-ai-基礎設施)
8. [評估 / 安全](#8-評估--安全)
9. [Prompt 工程 / 編排](#9-prompt-工程--編排)
10. [AI-Native 應用](#10-ai-native-應用)
11. [2025-2026 新星](#11-2025-2026-新星)
12. [Web Frameworks](#12-web-frameworks)
13. [Databases](#13-databases)
14. [DevOps / Infrastructure](#14-devops--infrastructure)
15. [Frontend Frameworks](#15-frontend-frameworks)
16. [Mobile](#16-mobile)
17. [Build Tools / Package Managers](#17-build-tools--package-managers)
18. [Observability](#18-observability)
19. [Security Tools](#19-security-tools)
20. [Emerging / Trendy](#20-emerging--trendy)
21. [Pattern 總整理](#pattern-總整理)
22. [推薦研究路線](#推薦研究路線)

---

## 1. LLM 推論引擎

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [ollama/ollama](https://github.com/ollama/ollama) | 166k | 9 | 精簡但完整 |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | 25k | **94** | 最多硬體平台：AMD/HPU/XPU/NPU/Xeon/H20/Blackwell |
| [mudler/LocalAI](https://github.com/mudler/LocalAI) | 44k | 32 | 多後端 container build、Intel docker cache、E2E mock/real 測試 |
| [NVIDIA/TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) | 13k | 22 | Blossom-CI + SonarQube 品質掃描 |
| [huggingface/text-generation-inference](https://github.com/huggingface/text-generation-inference) | 11k | 18 | HF 自家推論服務 CI |
| [InternLM/lmdeploy](https://github.com/InternLM/lmdeploy) | 8k | 22 | 中國 LLM 推論引擎 |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | 74k | 13 | 精簡（重度 CI 在外部跑）、Apple Silicon smoke test |

---

## 2. AI Agent 框架

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 183k | 39 | Claude + Copilot 雙 AI review、全端 CI、Claude Dependabot PR Review |
| [deepset-ai/haystack](https://github.com/deepset-ai/haystack) | 25k | 38 | 快慢測試分離、docstring 變更偵測、nightly pre-release |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 28k | 27 | 三語言（.NET/Python/Node）各自獨立品質管線、"Needs Port" label 系統 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 56k | 24 | 微軟多 agent 框架 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 47k | 21 | Canary release、nightly canary 檢查、測試時長追蹤 |
| [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 66k | 5 | 多 agent 協作 |
| [agno-agi/agno](https://github.com/agno-agi/agno) | 39k | 12 | 前身 Phidata |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 33k | 8 | Prompt 程式設計框架 |

---

## 3. RAG / 向量資料庫

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [milvus-io/milvus](https://github.com/milvus-io/milvus) | 44k | 34 | **Chaos engineering**：IO 延遲/記憶體壓力/網路分割/Pod kill |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 27k | 31 | 多語言 client 測試（Python/Go/Rust/JS）、SIMD/AVX 驗證、Spanner migration |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | 30k | 23 | Rust-native 聚焦型 CI |
| [weaviate/weaviate](https://github.com/weaviate/weaviate) | 16k | 14 | Go 向量 DB |
| [lancedb/lancedb](https://github.com/lancedb/lancedb) | 10k | 19 | 多語言 SDK |

---

## 4. 訓練 / 微調

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 69k | 13 | CUDA/NPU Docker 分離構建與測試 |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 59k | 4 | 極精簡 |
| [deepspeedai/DeepSpeed](https://github.com/deepspeedai/DeepSpeed) | 42k | 31 | 多 GPU：V100/A6000/MI200/XPU/HPU + Modal/AWS 雲端測試、pre-compiled op cache |
| [NVIDIA/Megatron-LM](https://github.com/NVIDIA/Megatron-LM) | 16k | 37 | Claude complexity label、oncall rotation、code freeze、API 相容性檢查、Slack sync |
| [axolotl-ai-cloud/axolotl](https://github.com/axolotl-ai-cloud/axolotl) | 12k | 14 | 微調工具 |
| [meta-pytorch/torchtune](https://github.com/meta-pytorch/torchtune) | 6k | 10 | Meta 官方微調 |
| [huggingface/transformers](https://github.com/huggingface/transformers) | 158k | 多 | 多 GPU 廠商 self-hosted runner、nightly builds、SSH debug runner、Slack 通知 |

---

## 5. AI Coding 工具

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | 70k | 33 | **Dogfooding**：用自己的 agent 修 issue + review PR + 評估 review 品質 |
| [continuedev/continue](https://github.com/continuedev/continue) | 32k | 43 | AI PR 評估、auto-fix failed tests、多 npm 套件發佈、多 IDE |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 43k | 12 | AI coding assistant |
| [TabbyML/tabby](https://github.com/TabbyML/tabby) | 33k | 16 | Rust + IntelliJ + VS Code + Vim 多 IDE 測試 |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 19k | 7 | SWE-bench agent |

---

## 6. Multimodal / Diffusion

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) | 107k | 24 | **Check AI Co-Authors**（審計 AI 貢獻）、OpenAPI 驗證、Windows release |
| [invoke-ai/InvokeAI](https://github.com/invoke-ai/InvokeAI) | 27k | 18 | Python + React 全端分離 CI、typegen/uv lock/LFS 檢查 |
| [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) | 162k | 6 | 162k 星但幾乎沒 CI — **反面教材** |
| [lllyasviel/Fooocus](https://github.com/lllyasviel/Fooocus) | 48k | 2 | 極簡 |

---

## 7. AI 基礎設施

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [kserve/kserve](https://github.com/kserve/kserve) | 5k | **44** | 每個 ML framework 獨立 Docker publisher（HF/vLLM/LightGBM/XGBoost/Sklearn/PMML...） |
| [ray-project/ray](https://github.com/ray-project/ray) | 42k | 7 | 重度 CI 在 Buildkite 外部跑 |
| [triton-inference-server/server](https://github.com/triton-inference-server/server) | 11k | 5 | NVIDIA 推論伺服器 |
| [bentoml/BentoML](https://github.com/bentoml/BentoML) | 9k | 6 | ML 服務化框架 |

---

## 8. 評估 / 安全

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [NVIDIA/NeMo-Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) | 6k | 25 | **Python 3.14 free-threaded 測試**、reusable test workflows、performance benchmark |
| [vibrantlabsai/ragas](https://github.com/vibrantlabsai/ragas) | 13k | 11 | RAG 評估框架 |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | 12k | 5 | LLM 評估標準 |
| [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails) | 7k | 12 | 輸出驗證框架 |

---

## 9. Prompt 工程 / 編排

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [microsoft/promptflow](https://github.com/microsoft/promptflow) | 11k | **124** | 每個 sample flow 各自一個 workflow — 暴力但有效確保文件品質 |
| [guidance-ai/guidance](https://github.com/guidance-ai/guidance) | 21k | 14 | 結構化輸出引擎 |
| [dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | 14k | 9 | 結構化生成 |
| [567-labs/instructor](https://github.com/567-labs/instructor) | 13k | 10 | 結構化 LLM 輸出 |
| [PrefectHQ/marvin](https://github.com/PrefectHQ/marvin) | 6k | 10 | AI 函式庫 |

---

## 10. AI-Native 應用

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [open-webui/open-webui](https://github.com/open-webui/open-webui) | 129k | 10 | 最熱門 AI 前端 |
| [lobehub/lobehub](https://github.com/lobehub/lobehub) | 74k | **46** | **9 個 Claude workflow**：review/翻譯/dedupe/triage/E2E/coverage/migration/PR assign |
| [janhq/jan](https://github.com/janhq/jan) | 41k | 37 | Tauri 跨平台 + Flatpak + Electron + AutoQA + Discord 通知 |
| [danny-avila/LibreChat](https://github.com/danny-avila/LibreChat) | 35k | 34 | Playwright E2E、Helm chart、i18n sync (Locize)、多 Docker 變體 |
| [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | 57k | 16 | 全端 AI 應用 |
| [ChatGPTNextWeb/NextChat](https://github.com/ChatGPTNextWeb/NextChat) | 88k | 9 | 跨平台 ChatGPT 前端 |

---

## 11. 2025-2026 新星

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 85k | 13 | AI 瀏覽器自動化、Claude Code 整合、雲端評估 |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 82k | 14 | **MCP Safety Scan** + Observatory Health Check |
| [openai/codex](https://github.com/openai/codex) | 68k | 29 | Rust + Nix + Buck2 + Bazel 四種 build system |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 20k | 12 | OpenAI Agent SDK |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 16k | 12 | Pydantic 生態 AI 框架 |

---

## 12. Web Frameworks

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [fastapi/fastapi](https://github.com/fastapi/fastapi) | 97k | 29 | 自動生成貢獻者頁面、changelog 自動化、bot-driven issue 管理 |
| [django/django](https://github.com/django/django) | 87k | 19 | 排程測試、Selenium 瀏覽器測試、benchmark |
| [spring-projects/spring-boot](https://github.com/spring-projects/spring-boot) | 80k | 14 | Snapshot 自動部署、system tests |
| [laravel/framework](https://github.com/laravel/framework) | 35k | 15 | 各子系統獨立 workflow（facades, queues）、多 DB 引擎測試 |

---

## 13. Databases

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [cockroachdb/cockroach](https://github.com/cockroachdb/cockroach) | 32k | 28 | 自動 backport cherry-pick（Blathers）、binary 相容性檢查 |
| [surrealdb/surrealdb](https://github.com/surrealdb/surrealdb) | 32k | 18 | Nix 可重現構建、supply chain security、SBOM |
| [pingcap/tidb](https://github.com/pingcap/tidb) | 40k | 10 | Bazel cross-compilation |

---

## 14. DevOps / Infrastructure

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [hashicorp/terraform](https://github.com/hashicorp/terraform) | 48k | 21 | **Equivalence test diffs**（驗證 plan 輸出）、Backport Assistant |
| [pulumi/pulumi](https://github.com/pulumi/pulumi) | 25k | 34 | PR comment 觸發 workflow（Command Dispatch）、自動更新 Homebrew |
| [argoproj/argo-cd](https://github.com/argoproj/argo-cd) | 22k | 18 | Container image **簽署**（cosign/Sigstore）、cherry-pick 自動化 |
| [containerd/containerd](https://github.com/containerd/containerd) | 21k | 23 | Protobuf 同步檢查、test image 構建 |

---

## 15. Frontend Frameworks

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [vercel/next.js](https://github.com/vercel/next.js) | 139k | 多 | Reusable workflows、flaky test retry、code freeze、Turbopack 整合測試 |
| [angular/angular](https://github.com/angular/angular) | 100k | 21 | OpenSSF Scorecard、Google 內部測試橋接 |
| [sveltejs/svelte](https://github.com/sveltejs/svelte) | 86k | 9 | **pkg.pr.new** — 每個 PR 自動發佈臨時 npm 套件 |
| [vuejs/core](https://github.com/vuejs/core) | 53k | 13 | **Ecosystem CI** — PR 自動觸發下游專案（Nuxt/Vite/Vue Router）測試 |

---

## 16. Mobile

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [flutter/flutter](https://github.com/flutter/flutter) | 176k | 18 | GitHub ↔ Google 內部 repo 同步 mirror |
| [facebook/react-native](https://github.com/facebook/react-native) | 126k | 32 | 重度 issue triage 自動化、auto-rebase |
| [expo/expo](https://github.com/expo/expo) | 48k | **58** | Monorepo 教科書：每平台、每 package 獨立 workflow |

---

## 17. Build Tools / Package Managers

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [oven-sh/bun](https://github.com/oven-sh/bun) | 88k | 35 | 跨平台 Zig/C++ 構建、release artifact 驗證 |
| [astral-sh/uv](https://github.com/astral-sh/uv) | 82k | 27 | Dev binary 快速構建、Docker multi-arch |
| [astral-sh/ruff](https://github.com/astral-sh/ruff) | 47k | 多 | 每日 fuzzing、記憶體用量追蹤、mypy_primer 生態驗證 |
| [vercel/turborepo](https://github.com/vercel/turborepo) | 30k | 17 | **Cache 正確性驗證**、branch cache cleanup |
| [pnpm/pnpm](https://github.com/pnpm/pnpm) | 34k | 11 | Reusable test workflow、benchmark vs npm/yarn |
| [gradle/gradle](https://github.com/gradle/gradle) | 18k | 28 | Contributor CI（較輕）vs Full CI 分離、IDE team 通知 |

---

## 18. Observability

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [grafana/grafana](https://github.com/grafana/grafana) | 73k | **144** | **全球最多 workflow**，企業級 CI 標竿 |
| [prometheus/prometheus](https://github.com/prometheus/prometheus) | 63k | 21 | **Prombench** 比較叢集、AI Security Review（Barry）、buf.build protobuf 驗證 |
| [open-telemetry/opentelemetry-collector](https://github.com/open-telemetry/opentelemetry-collector) | 7k | 35 | 自動偵測 breaking changes 並通知下游（Inform Incompatible PRs） |

---

## 19. Security Tools

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | 34k | 29 | Helm chart publishing、雙文件部署（dev + stable） |
| [falcosecurity/falco](https://github.com/falcosecurity/falco) | 9k | 20 | Engine version ABI 相容性檢查、Bump Libs 自動更新 |
| [goreleaser/goreleaser](https://github.com/goreleaser/goreleaser) | 16k | 多 | 6+ 安全工具（Gitleaks/Grype/govulncheck/SBOM/Scorecard） |

---

## 20. Emerging / Trendy

| Repo | Stars | Workflows | 亮點 |
|---|---|---|---|
| [zed-industries/zed](https://github.com/zed-industries/zed) | 78k | **58** | **Randomized Tests**（fuzz in CI）、collaboration server 部署 |
| [openclaw/openclaw](https://github.com/openclaw/openclaw) | 339k | 61 | AI code review (Claude + Codex)、多平台建置、5+ 安全掃描 |
| [denoland/deno](https://github.com/denoland/deno) | 106k | 多 | **6 階段 release train**（start → bump → cargo → npm → post → promote） |
| [tauri-apps/tauri](https://github.com/tauri-apps/tauri) | 105k | 多 | 每元件獨立 lint/test、covector 版本管理 |
| [Effect-TS/effect](https://github.com/Effect-TS/effect) | 14k | 8 | TypeScript nightly 測試、release queue 批次發佈 |
| [honojs/hono](https://github.com/honojs/hono) | 30k | 6 | 精簡高效 — 證明好設計不需要幾十個 workflow |
| [rust-lang/rust](https://github.com/rust-lang/rust) | 112k | 多 | 可重現性檢查、post-merge 分析 |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | 62k | 少 | 跨平台 cross-compile release 範本，常被參考 |
| [biomejs/biome](https://github.com/biomejs/biome) | — | 多 | 9 種語言各自 benchmark、stable/beta/preview 多通道發佈 |
| [oxc-project/oxc](https://github.com/oxc-project/oxc) | 20k | 多 | Callgrind/Valgrind profiling、Miri 記憶體安全、reusable NAPI release |
| [NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw) | 17k | 15 | E2E 測試、docs preview、PR limit 治理 |

---

## Pattern 總整理

### CI/CD 架構模式

| Pattern | 最佳範例 | 說明 |
|---|---|---|
| AI-as-CI-agent | **LobeChat** (9 Claude workflows), **OpenHands** | 用 AI 做 code review / triage / 翻譯 / dedupe |
| Dogfooding | **OpenHands** | 用自己的 agent 修 issue + review PR |
| Chaos engineering | **Milvus** | IO 延遲 / 記憶體壓力 / 網路分割 / Pod kill |
| 多硬體平台矩陣 | **SGLang** (94 workflows) | AMD/HPU/XPU/NPU/Xeon/H20/Blackwell |
| 每 sample 各自 CI | **Promptflow** (124 workflows) | 確保每個文件範例永遠可用 |
| 多 build system | **OpenAI Codex** | Rust + Nix + Buck2 + Bazel |
| Ecosystem CI | **Vue.js Core**, **Svelte** | PR 自動觸發下游專案測試 |
| PR 即套件預覽 | **Svelte** (pkg.pr.new) | 每個 PR 自動發佈臨時 npm 套件 |
| Reusable workflows | **next.js**, **oxc** | 共用 build workflow 避免重複 |
| Multi-stage release train | **Deno** (6 階段) | start → bump → cargo → npm → post → promote |
| 多通道發佈 | **Biome** | stable / beta / preview channels |
| Container 簽署 | **Argo CD** (cosign/Sigstore) | Supply chain security |
| Fuzz / randomized testing | **Zed**, **Ruff** | CI 中跑 fuzz testing |
| Performance tracking | **oxc** (Callgrind), **Biome** (per-lang bench) | 效能回歸偵測 |
| Cache 正確性驗證 | **Turborepo** | 對 build cache 工具至關重要 |
| AI 貢獻審計 | **ComfyUI** (Check AI Co-Authors) | 追蹤 AI 生成的程式碼 |
| Python 前瞻測試 | **NeMo-Guardrails** | Python 3.14 free-threaded |
| AI Security Review | **Prometheus** (Barry) | AI 自動安全審查 |
| Flaky test retry | **next.js** | 獨立 retry workflow 處理不穩定測試 |
| Cross-version compat | **MLflow** (77 workflows) | 多 Python/dependency 版本矩陣 |

### 規模排行 Top 10

| # | Repo | Workflows |
|---|---|---|
| 1 | Grafana | 144 |
| 2 | Promptflow | 124 |
| 3 | SGLang | 94 |
| 4 | MLflow | 77 |
| 5 | OpenClaw | 61 |
| 6 | Expo | 58 |
| 7 | Zed | 58 |
| 8 | LobeChat | 46 |
| 9 | KServe | 44 |
| 10 | Continue | 43 |

---

## 現有相關工具與市場缺口

### Repo 探索 / 趨勢追蹤

| 工具 | 連結 | 說明 |
|---|---|---|
| **OSSInsight** | [ossinsight.io](https://ossinsight.io/) | 分析 10B+ GitHub events，可比較專案、追蹤趨勢，支援自然語言查詢 |
| **Trendshift** | [trendshift.io](https://trendshift.io/) | GitHub Trending 替代品，用每日互動指標做一致性評分 |
| **GitHub Explore** | [github.com/explore](https://github.com/explore) | 官方推薦與趨勢，個人化推薦 |
| **ReadmeCodegen Finder** | [readmecodegen.com/open-source-finder](https://www.readmecodegen.com/open-source-finder) | 用演算法分析適合貢獻的 repo |

### Awesome 清單（人工整理）

| 清單 | 連結 | 說明 |
|---|---|---|
| **awesome-actions** | [sdras/awesome-actions](https://github.com/sdras/awesome-actions) | 最知名的 GitHub Actions 整理，分類齊全 |
| **awesome-github-actions** | [Alliedium/awesome-github-actions](https://github.com/Alliedium/awesome-github-actions) | Workflow 範例集，展示各種 CI/CD 用例 |
| **awesome-github-actions** | [brandonhimpfen/awesome-github-actions](https://github.com/brandonhimpfen/awesome-github-actions) | Actions 工具、資源與 workflow 清單 |
| **awesome-ci** | [ligurio/awesome-ci](https://github.com/ligurio/awesome-ci) | CI 服務與工具完整列表 |
| **awesome-workflow-engines** | [meirwah/awesome-workflow-engines](https://github.com/meirwah/awesome-workflow-engines) | 開源 workflow 引擎清單 |
| **awesome-workflow-automation** | [dariubs/awesome-workflow-automation](https://github.com/dariubs/awesome-workflow-automation) | Workflow 自動化軟體與工具 |

### CI/CD 安全掃描

| 資源 | 連結 | 說明 |
|---|---|---|
| **GH Actions 安全掃描器研究** | [arxiv.org/html/2601.14455v2](https://arxiv.org/html/2601.14455v2) | 學術研究，從 30 個候選篩選出 9 個 workflow 安全掃描器 |
| **GitHub Actions Observability** | [balena.io blog](https://blog.balena.io/github-actions-observability/) | GitHub Actions 可觀測性實踐 |

### Copilot / AI 輔助 CI

| 資源 | 連結 | 說明 |
|---|---|---|
| **awesome-copilot CI/CD instructions** | [github/awesome-copilot](https://github.com/github/awesome-copilot/blob/main/instructions/github-actions-ci-cd-best-practices.instructions.md) | GitHub 官方 Copilot CI/CD 最佳實踐指引 |

### 市場缺口分析

| 功能 | 現有工具 | 狀態 |
|---|---|---|
| 找熱門 repo | OSSInsight, Trendshift | ✅ 已有 |
| 整理好用的 Actions | awesome-actions 等 | ✅ 已有（但人工維護） |
| 分析單一 repo 的 CI | GitHub 內建 Insights | ✅ 已有 |
| **跨 repo 抓取 + 比較 workflow patterns** | — | ❌ 沒人做 |
| **自動歸納 CI/CD 最佳實踐模式** | — | ❌ 沒人做 |
| **依技術棧推薦 workflow 範本** | — | ❌ 沒人做 |

> **結論：** 現有工具要嘛是「找 repo」（OSSInsight），要嘛是「列 Actions」（awesome 清單），
> 但沒有人自動跨專案抓取 workflow、分析 CI/CD pattern、歸納最佳實踐。這是明確的市場空缺。

---

## 推薦研究路線

### 如果你想學...

| 目標 | 建議從這些開始 |
|---|---|
| **入門 GitHub Actions** | Hono (6), Svelte (9) — 精簡但完整 |
| **Monorepo CI** | Expo (58), next.js, Semantic Kernel |
| **AI 驅動的 CI** | LobeChat, OpenHands, AutoGPT |
| **Release 自動化** | Deno (6 階段), Biome (多通道), goreleaser |
| **多平台 / 跨硬體** | SGLang, DeepSpeed, llama.cpp |
| **安全 / Supply chain** | goreleaser, Argo CD, SurrealDB |
| **效能監控 in CI** | oxc, Biome, Ruff, Prometheus |
| **Chaos / 穩定性測試** | Milvus, Zed (randomized tests) |
| **Docker / Container 管線** | LocalAI, KServe, OpenClaw |
| **社群自動化** | FastAPI, React Native, next.js |

---

## 產品方向發想

### 開發者工具

| # | 方向 | 說明 | 參考 |
|---|---|---|---|
| 1 | **Workflow Generator** | 輸入技術棧（如 Rust + Docker + multi-platform），自動從真實專案中組合出最佳 workflow 範本 | 目前只有 GitHub 的 starter workflow，沒有跨專案學習的版本 |
| 2 | **CI Cost Optimizer** | 分析 workflow 的 runner 時間、並行效率、cache 命中率，建議省錢方案 | Turborepo 的 cache 正確性驗證可參考 |
| 3 | **Workflow Migrator** | 跨 CI 平台轉換（GitLab CI → GitHub Actions → CircleCI），參考同類專案的寫法 | 現有轉換工具只做語法翻譯，不參考最佳實踐 |

### AI + CI/CD

| # | 方向 | 說明 | 參考 |
|---|---|---|---|
| 4 | **AI PR Reviewer Starter Kit** | 一鍵幫專案加上 Claude/Copilot code review workflow | LobeChat 有 9 個 Claude workflow，但設定門檻高 |
| 5 | **CI Copilot** | 寫完程式碼後，AI 自動建議要新增或修改哪些 workflow（偵測到新增 Dockerfile → 建議加 container scan） | 目前沒有 AI 主動建議 CI 配置的工具 |
| 6 | **Flaky Test Detective** | 跨 repo 收集 flaky test pattern，用 AI 分類根因並建議修復策略 | next.js 的 retry workflow 是治標，根因分析是治本 |

### 資料產品 / 內容

| # | 方向 | 說明 | 參考 |
|---|---|---|---|
| 7 | **CI/CD Benchmark Report** | 定期發佈月報/季報：哪些 pattern 在上升、哪些被淘汰、各語言生態的 CI 趨勢 | 類似 OSSInsight 的趨勢報告，但聚焦 CI/CD |
| 8 | **Workflow Changelog** | 追蹤知名專案的 `.github/workflows/` 變更，發現新 pattern 時自動通知 | 像 GitHub Release watch，但針對 CI 配置變更 |
| 9 | **Security Posture Dashboard** | 掃描熱門專案的 CI 安全配置（secrets 處理、permission、supply chain），產出評分排行 | goreleaser 的 6+ 安全工具可作為評分基準 |

### 社群 / 教育

| # | 方向 | 說明 | 參考 |
|---|---|---|---|
| 10 | **CI/CD Pattern Library** | 互動式網站，每個 pattern 有真實專案範例、適用場景、複製即用的 YAML | awesome 清單的升級版，加上互動搜尋 |
| 11 | **Workflow Diff Tool** | 選兩個專案，並排比較 CI 策略差異 | 像 OSSInsight 比 repo，但專注 workflow |

### 最有潛力的三個方向

| 排名 | 方向 | 理由 |
|---|---|---|
| 🥇 | **Workflow Changelog (#8)** | 低成本高價值，git watch `.github/workflows/` 就能做，開發者會訂閱，可快速驗證需求 |
| 🥈 | **AI PR Reviewer Starter Kit (#4)** | LobeChat 證明了需求，但設定門檻高，一鍵方案有明確市場 |
| 🥉 | **CI/CD Pattern Library (#10)** | awesome 清單的進化版，加上互動搜尋和真實 YAML，SEO 流量好，可長期累積 |

### 命名參考

| 產品定位 | 候選名稱 |
|---|---|
| 跨 repo workflow 分析 | **CIHarvest** / **WorkflowLens** / **PipelinePedia** |
| Workflow 變更追蹤 | **CIDiff** / **WorkflowWatch** / **PipelinePulse** |
| AI 驅動 CI 設定 | **CIPilot** / **FlowForge** / **ActionSmith** |

---

## 延伸觀察面向（Beyond CI/CD）

除了 GitHub Actions workflow，還有更多面向值得跨專案觀察，對開發者同樣有幫助。

### 程式碼品質與規範

| # | 觀察面向 | 說明 | 觀察目標 |
|---|---|---|---|
| 1 | **Linter / Formatter 配置** | 各專案用什麼 lint 規則、怎麼配 ESLint/Ruff/Clippy，哪些規則被關掉 | `.eslintrc`, `ruff.toml`, `clippy.toml`, `biome.json` |
| 2 | **Pre-commit hooks** | 都掛了什麼檢查、怎麼組合、效能如何 | `.pre-commit-config.yaml`, `.husky/` |
| 3 | **PR / Issue 模板** | 大專案怎麼設計模板引導貢獻者寫出好的描述 | `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/` |

### 專案架構

| # | 觀察面向 | 說明 | 觀察目標 |
|---|---|---|---|
| 4 | **Monorepo 結構** | 目錄怎麼切、package 怎麼拆、workspace 怎麼配 | `turbo.json`, `nx.json`, `pnpm-workspace.yaml`, `Cargo.toml` workspace |
| 5 | **設定檔演化** | 配置趨勢，哪些選項在流行、哪些被棄用 | `tsconfig.json`, `Cargo.toml`, `pyproject.toml`, `vite.config.ts` |
| 6 | **依賴管理策略** | lockfile 策略、Renovate/Dependabot 配置、版本固定 vs 浮動 | `renovate.json`, `.github/dependabot.yml`, lockfile 策略 |

### 文件與開發者體驗

| # | 觀察面向 | 說明 | 觀察目標 |
|---|---|---|---|
| 7 | **CONTRIBUTING.md 模式** | 成功的開源專案怎麼降低貢獻門檻 | `CONTRIBUTING.md`, `DEVELOPMENT.md` |
| 8 | **開發環境設定** | Devcontainer、Nix flakes、Docker Compose 的 DX 設計 | `.devcontainer/`, `flake.nix`, `docker-compose.yml` |
| 9 | **CHANGELOG 自動化** | Conventional Commits + changeset/release-please 的實踐方式 | `.changeset/`, `.release-please-manifest.json`, `cliff.toml` |

### 安全實踐

| # | 觀察面向 | 說明 | 觀察目標 |
|---|---|---|---|
| 10 | **Security Policy** | 怎麼寫漏洞揭露流程、怎麼設計回報機制 | `SECURITY.md` |
| 11 | **權限最小化** | GitHub Actions 的 `permissions` 設定、CODEOWNERS 用法 | workflow 的 `permissions:` 欄位, `CODEOWNERS` |
| 12 | **供應鏈安全** | SBOM 生成、簽署、dependency review 的實際配置 | `cosign`, `syft`, `dependency-review-action` |

### 社群治理

| # | 觀察面向 | 說明 | 觀察目標 |
|---|---|---|---|
| 13 | **Bot 與自動化** | 哪些 bot 在用、怎麼配、效果如何 | stale bot, labeler, auto-assign, welcomebot |
| 14 | **Release 策略** | 語義版本、release notes 自動生成、多通道發佈 | `release-please`, `changesets`, `semantic-release`, `goreleaser` |
| 15 | **RFC / ADR 流程** | 大專案怎麼做技術決策記錄 | `docs/rfcs/`, `docs/adr/`, `architectural-decision-records/` |

### 延伸面向中最值得做成產品的三個

| 排名 | 方向 | 理由 |
|---|---|---|
| 🥇 | **設定檔趨勢追蹤 (#5)** | 開發者最常 Google 的就是「怎麼配 tsconfig / pyproject.toml」，跨專案比較需求巨大 |
| 🥈 | **Monorepo 結構分析 (#4)** | Monorepo 越來越普及但沒有好的參考工具，只能一個一個翻 repo |
| 🥉 | **依賴管理策略 (#6)** | Renovate/Dependabot 配置五花八門，整理最佳實踐對所有團隊都有價值 |

### 全產品方向總覽

結合 CI/CD 與延伸面向，完整的產品可能性：

| 類別 | 產品方向 | 數量 |
|---|---|---|
| 開發者工具 | Workflow Generator, CI Cost Optimizer, Workflow Migrator | 3 |
| AI + CI/CD | AI PR Reviewer Kit, CI Copilot, Flaky Test Detective | 3 |
| 資料產品 | CI/CD Benchmark Report, Workflow Changelog, Security Dashboard | 3 |
| 社群 / 教育 | Pattern Library, Workflow Diff Tool | 2 |
| 設定 / 架構觀察 | 設定檔趨勢, Monorepo 分析, 依賴管理策略 | 3 |
| 品質 / 安全 | Linter 配置比較, 供應鏈安全評分, 權限最小化檢查 | 3 |
| 開發者體驗 | DX 環境設定範本, CONTRIBUTING 範本, CHANGELOG 自動化 | 3 |
| **合計** | | **20 個方向** |
