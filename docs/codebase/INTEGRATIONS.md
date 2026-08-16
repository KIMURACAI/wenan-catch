# External Integrations 外部集成

## Core Sections (Required)

### 1) Integration Inventory

| System | Type | Purpose | Auth model | Criticality | Evidence |
|--------|------|---------|------------|-------------|----------|
| 抖音网页版 douyin.com | Web 爬取（Playwright） | 采集目标用户/话题视频与口播文案 | Cookie（扫码登录持久化 `data/cookies/douyin_cookies.json`） | 高（整条主线依赖） | `browser/login.py`、`extractors/interceptor.py` |
| 飞书开放平台 | REST API | ①多维表格读采集目标 ②文档写日报 | 自建应用 App ID/Secret → tenant_access_token（2h 自动刷新） | 高（日报输出） | `feishu/auth.py`、`feishu/bitable.py`、`feishu/document.py` |
| 火山引擎 BigModel ASR | REST API（豆包同款引擎） | 视频音频 → 中文转写 | Access Key/Secret Key + App ID/App Key（签名） | 高（实际 ASR 引擎，`pipeline/orchestrator.py:281` 引用 volc_asr） | `transcriber/volc_asr.py` |
| DeepSeek API | REST API（OpenAI 兼容 chat/completions） | 文案 AI 整理（`--ai-refine` 启用） | Bearer `DEEPSEEK_API_KEY` | 中（可选功能） | `ai/provider.py:17-18` |
| 火山方舟（Ark） | [TODO] 未发现调用代码 | 仅 `.env` 配置 `VOLC_ARK_API_KEY` 预留 | [TODO] | 低 | `.env` 键名 |
| OpenAI Whisper | 本地模型推理 | 备用语音转文字（tiny 模型） | 无（本地） | 低（当前流程未使用，属备选） | `transcriber/stt.py`、`config/settings.py:72-74` |
| 豆包 AI 生图 | [TODO] 生成流程未在代码中（产物在 comic_doubao/） | 漫画配图生成 | [ASK USER] 生成方式待确认 | 中（内容线素材来源） | `comic_doubao/*.png` |

### 2) Data Stores

| Store | Role | Access layer | Key risk | Evidence |
|-------|------|--------------|----------|----------|
| SQLite `data/wenan_catch.db` | 主线数据：posts（含状态机/转写/润色）、run_logs、scrape_targets 缓存 | `storage/repository.py`（唯一 CRUD） | 单文件单机，无备份机制 | `storage/schema.sql`、`storage/database.py` |
| 文件缓存 `cache/videos/`、`cache/audios/` | 下载视频与提取音频的临时缓存 | `transcriber/downloader.py` | 清理失效：`cache/videos` 残留 43-95MB 视频（scan 最大文件榜） | `transcriber/downloader.py` docstring |
| JSON 中间文件 | 内容线各阶段产物（`qimen_cases.json` 等） | 各脚本直接读写 | 无 schema 校验、散落根目录 | `extract_qimen.py:10` |

### 3) Secrets and Credentials Handling

- 凭证来源：`.env`（pydantic-settings 加载，`config/settings.py:19-23`）+ `config/config.yaml`（仅非敏感参数）
- 硬编码检查：**未发现密钥硬编码**；但内容线脚本硬编码机器路径（`extract_qimen.py:9`）
- 轮换/生命周期：未知 [TODO]；飞书 token 自动刷新（`feishu/auth.py`），抖音 Cookie 失效需人工重扫码（`pipeline/orchestrator.py:92-96` 检测）
- 风险：`.gitignore` 存在（含 .env 保护）但**项目不是 git 仓库**，若未来 init 需确认 .gitignore 覆盖（见 CONCERNS）

### 4) Reliability and Failure Behavior

- 重试/退避：部分实现——视频下载多 URL 尝试（`pipeline/orchestrator.py:301-309`）、失败任务 `increment_retry` 计数（`storage/repository.py`）、目标间随机 5-8s 延时（`pipeline/orchestrator.py:104-107`）；DeepSeek 调用无重试（`ai/provider.py` 直接抛 AIError）
- 超时策略：httpx 调用 60s（`ai/provider.py:42`）；Playwright 页面 30s（`config/settings.py:51`）；下载多 URL 兜底
- 熔断/降级：无熔断器；有**降级链**——飞书拉目标失败回落本地缓存（`pipeline/orchestrator.py:164-171`）、Whisper↔火山双引擎、飞书 SDK 缺失仅告警（`pipeline/orchestrator.py:531-532`）

### 5) Observability for Integrations

- 对外调用日志：有——loguru 记录失败原因与状态（如 `ai/provider.py:48-52` 记 HTTP 状态码）
- 指标/追踪：无（无 APM/指标导出）
- 可见性缺口：ASR/API 调用耗时不记；run_logs 只记结果不记成本；内容线脚本仅 print 摘要

### 6) Evidence

- `feishu/auth.py`、`ai/provider.py`、`transcriber/volc_asr.py`
- `.env` / `.env.template`、`config/settings.py`
- `storage/schema.sql`
- `docs/codebase/.codebase-scan.txt`（ENVIRONMENT VARIABLE TEMPLATES 段）
