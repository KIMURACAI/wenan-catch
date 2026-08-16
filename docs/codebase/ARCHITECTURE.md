# Architecture 架构

> 两个子系统的架构差异很大：主线是**分层 + 编排器**架构；内容制作线是**阶段式脚本流水线**（JSON 中间文件 + 断点续跑）。

## Core Sections (Required)

### 1) Architectural Style

- 主线风格：**分层（layer-based）+ Orchestrator 编排**。`config/models/storage/browser/extractors/transcriber/content_engine/feishu` 按职责分层，`pipeline/orchestrator.py` 是唯一总控。
- 依据：`pipeline/orchestrator.py:1-13` docstring 明确"协调整个采集流程……不处理业务细节、不直接读写数据库、不管理浏览器生命周期细节"；各层 `__init__.py` docstring（"浏览器自动化模块""语音转文字模块"等）。
- 内容线风格：**线性阶段流水线**。每阶段独立脚本，中间结果落 JSON 文件，支持 `--from N` 断点续跑（`pdf2ppt/README.md:26-29`）。
- 主要约束：
  1. 单机 Windows 运行，无服务化（无 Docker/CI，scan 确认）；
  2. 抖音反爬：全流程带随机延时与反检测（`config/settings.py:56-65`）；
  3. 内容线"源文字一字不改"原则（`docx2ppt/parse.py:11`、`extract_qimen.py:3`）。

### 2) System Flow

**主线（一次采集运行）**：

```text
main.py (once)
  → Orchestrator.run()
      → [1] feishu.bitable 拉目标列表（失败回落本地 scrape_targets 表）
      → [2] browser 建上下文 → 检查登录（Cookie）
      → [3] extractors 逐目标采集（API 拦截）→ pipeline.dedup 去重 → storage 保存
      → [4] transcriber：下载视频 → ffmpeg 提音频 → 火山 ASR → refiner 精炼
      → [5] content_engine：DeepSeek 整理 → quality_checker 过改检测
      → [6] feishu.document：按账号追加到飞书文档（日报）
      → storage.run_logs 记运行日志
```

证据链：`main.py:108-121` → `pipeline/orchestrator.py:77-158`（第 1-5 步注释）→ `extractors/interceptor.py`（API 拦截）→ `transcriber/volc_asr.py` → `content_engine/pipeline.py:26-51` → `feishu/document.py`。

**内容线（预测案例课程，当前活跃）**：

```text
预测案例92-168.docx
  → extract_qimen.py → qimen_cases.json（结构化：简介/理论/12节/20案例/排盘9宫格）
      → build_qimen_html.py → 奇门遁甲预测案例-课程.html → PDF
  → docx2ppt/parse.py → Deck 模型（Section/Case/ParamBlock/CellData）
      → docx2ppt/deck.py + chart.py → 81work/预测案例_输出.pptx
  验证环：validate_qimen.py / verify_dipan.py / final_verify.py（排盘规则重算比对）
         verify_ppt.py / audit_chart.py / detect_overflow.ps1（PPT 完整性+溢出）
```

### 3) Layer/Module Responsibilities

| Layer or module | Owns | Must not own | Evidence |
|-----------------|------|--------------|----------|
| Orchestrator（pipeline/） | 流程顺序、状态机推进、异常兜底 | 业务细节、SQL、浏览器细节 | `pipeline/orchestrator.py:10-13` |
| Repository（storage/） | 全部 CRUD | — | `storage/repository.py:1-6` |
| BrowserManager | 浏览器生命周期、上下文、Cookie | 业务数据解析 | `browser/manager.py` docstring |
| Interceptor/Extractors | 抖音 API 响应 → Post | 去重、落库 | `extractors/interceptor.py` |
| Transcriber | 下载/音频/ASR/精炼 | AI 改写（归 content_engine） | `transcriber/refiner.py`、`content_engine/pipeline.py:1-4` |
| ContentEngine | AI 整理 + 过改检测 | 存储、采集 | `content_engine/pipeline.py` |
| Feishu 模块 | 认证/表格/文档/格式化 | 业务判断 | `feishu/*.py` docstring |
| docx2ppt / pdf2ppt | 各自文档→PPT 转换 | （互不共享代码，边界割裂） | `docx2ppt/parse.py`、`pdf2ppt/run_pipeline.py` |

### 4) Reused Patterns

| Pattern | Where found | Why it exists |
|---------|-------------|---------------|
| Repository 模式 | `storage/repository.py` | 唯一 SQL 入口，业务层不写 SQL |
| Orchestrator/编排器 | `pipeline/orchestrator.py` | 集中流程控制，可 dry-run/断点 |
| Adapter 模式 | `transcriber/volc_asr.py`（替代 `stt.py`）、`feishu/auth.py` | 换引擎/换 SDK 不影响上游 |
| 阶段流水线 + JSON 中间件 | `pdf2ppt/`、`extract_qimen.py`→`build_qimen_html.py` | 断点续跑、中间结果可审计 |
| 规则+AI 双模式 | `pdf2ppt/clean.py`（rule/llm 双清理模式） | 无 API 时兜底，有 API 时提质（README:75-83） |
| 验证环（verify/audit/validate 脚本） | 根目录 + `81work/` | 内容正确性靠独立重算比对（排盘规则、文本逐字） |
| 状态机 | `models/schemas.py` TaskStatus（new→downloading→…→done/failed） | 断点续传与重试 |

### 5) Known Architectural Risks

- **无版本控制**（scan：Not a git repository）：任何误改不可回滚；产物靠 `_backup/_backup2/_原始` 文件名手工备份（如 `output_final_backup.pptx`）。
- **双转换流水线重复造轮子**：`pdf2ppt/` 与 `docx2ppt/` 都做"文档→Kami 风格 PPT"，代码不共享，改动需双份维护。
- **入口碎片化**：根目录 60+ 独立脚本，运行顺序靠人记忆；`content_engine/__pycache__` 里有已删除模块（classifier/analyzer/template_manager）的残留，说明引擎经历过未收尾的重构。
- **单机单点**：SQLite + 本机定时任务，无容灾；Cookie 过期则整条采集线停摆（`pipeline/orchestrator.py:92-96`）。

### 6) Evidence

- `pipeline/orchestrator.py`（主流程）
- `main.py`（入口）
- `extract_qimen.py` / `build_qimen_html.py` / `docx2ppt/parse.py`（内容线流程）
- `docs/codebase/.codebase-scan.txt`（ENTRY POINTS / GIT RECENT COMMITS / MONOREPO SIGNALS 段）
- `pdf2ppt/README.md`
