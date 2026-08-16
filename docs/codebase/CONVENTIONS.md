# Coding Conventions 编码约定

> 无 linter/formatter 配置（scan 确认），约定从源码 docstring 与命名一致性推断，并标注例外。

## Core Sections (Required)

### 1) Naming Rules

| Item | Rule | Example | Evidence |
|------|------|---------|----------|
| 文件 | snake_case（下划线）；根目录任务脚本用动词前缀 | `user_extractor.py`、`build_qimen_html.py`、`verify_dipan.py` | 全目录命名 |
| 类 | PascalCase | `Orchestrator`、`BrowserManager`、`QualityChecker`、`CellData` | `pipeline/orchestrator.py:36`、`browser/manager.py` |
| 函数/方法 | snake_case；私有方法 `_` 前缀 | `_scrape_target`、`_run_asr_pipeline`、`run_once` | `pipeline/orchestrator.py:208,264` |
| 常量 | UPPER_SNAKE_CASE | `MAX_NEW_PER_TARGET`、`SENT_END`、`POS_PALACE` | `pipeline/orchestrator.py:238`、`extract_qimen.py:12` |
| 环境变量 | UPPER_SNAKE，按服务前缀分组 | `FEISHU_*`、`VOLC_*`、`DEEPSEEK_API_KEY` | `.env` |
| 配置字段 | snake_case，Pydantic alias 接环境变量 | `feishu_app_id` ← `FEISHU_APP_ID` | `config/settings.py:26-30` |
| 数据表/列 | snake_case | `posts.transcribed_text_raw`、`run_logs.posts_collected` | `storage/schema.sql` |

### 2) Formatting and Linting

- Formatter：**未配置**（无 .prettierrc/black/pyproject，scan "No linting or formatting config files found"）
- Linter：**未配置**
- 观察到的风格规范（人工一致性）：
  1. 缩进 4 空格；模块 docstring 放文件首，用中文描述职责与边界（"负责/不做"式）
  2. 中文标点统一（`extract_qimen.py:56-61` 有 normalize 函数把半角逗号转全角——内容域要求）
  3. 关键数字用命名常量（`MAX_NEW_PER_TARGET = 3`）而非魔法数字（仅主线，内容线脚本偶有硬编码）
- Run commands：无（无配置即无 lint 命令）

### 3) Import and Module Conventions

- 导入分组：标准库 → 第三方 → 本地模块（如 `pipeline/orchestrator.py:15-33`）
- 绝对导入为主：`from config import settings`、`from ai.provider import AIProvider`
- 路径兜底：入口脚本用 `sys.path.insert(0, str(Path(__file__).resolve().parent))`（`main.py:22-23`）；独立脚本（`81work/verify_ppt.py:3`）同法
- 重型依赖惰性导入：函数内 import（`from transcriber.downloader import VideoDownloader` 出现在方法体内，`pipeline/orchestrator.py:279`），推测为加速启动/容错可选依赖
- 无 barrel export 约定（各 `__init__.py` 仅一行中文 docstring）

### 4) Error and Logging Conventions

- 错误策略：
  - 主线：统一异常类型定义在 `utils/exceptions.py`（"所有模块只能抛出这些异常"，docstring 明示）；Orchestrator 逐目标 try/except 兜底，失败目标记录 `failed_targets` 不中断整体（`pipeline/orchestrator.py:255-258`）
  - 内容线：宽松容错——解析失败"只记 warning 不中断"（`docx2ppt/parse.py:11`）；验证脚本打印 ✗/✓ 明细
- 日志：**loguru 唯一**。控制台彩色 + 文件按天轮转（保留 7 天），格式见 `main.py:41-56`
- 日志语言：中文 + emoji 状态（✅/❌/📊）；进度用 `i+1/total` 模式
- 敏感数据脱敏：未见专门机制；`.env` 不进入日志，但 API 异常仅记 status code（`ai/provider.py:49-52`）——[TODO] 未系统审计日志是否泄露 key

### 5) Testing Conventions

- 无测试框架、无测试目录（详见 TESTING.md）
- 内容线以"验证脚本"替代单元测试：`verify_*.py`、`validate_qimen.py`、`audit_*.py`，规则是**独立重算比对**（如 `final_verify.py` 用排盘规则重算地盘与提取结果逐格比对）

### 6) Evidence

- `pipeline/orchestrator.py`（命名/错误/日志代表）
- `config/settings.py`（alias 映射）
- `utils/exceptions.py`、`main.py:32-56`（日志配置）
- `extract_qimen.py:56-61`、`docx2ppt/parse.py:1-11`（内容线约定）
- `docs/codebase/.codebase-scan.txt`（LINTING 段：无配置）

## Extended Sections

### 已知的约定违背（待清理项）

| 违背 | 位置 | 说明 |
|------|------|------|
| 硬编码绝对路径 | `extract_qimen.py:9`（`C:\Users\Kimura\...`）、`81work/verify_ppt.py:7-8` | 机器相关，不可移植 |
| 魔法数字与内联样式 | `build_qimen_html.py:20-48`（CSS 常量）、`verify_ppt.py:69-84`（字号估算公式） | 内容线脚本普遍 |
| 遗留死代码 | `extract_qimen.py:202-209`（无效循环 `if idx not in [...] : pass`） | 未清理 |
