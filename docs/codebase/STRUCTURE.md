# Codebase Structure 目录结构

> 工作目录 `E:\wenan catch`（约 1900 文件）实际是**两代工作共存**：
> ① 抖音文案采集系统（Python 包，`main.py` 为唯一入口）；② 国学课程内容制作（根目录散落的一次性脚本 + `pdf2ppt/`、`docx2ppt/`、`81work/` 三个工作区）。

## Core Sections (Required)

### 1) Top-Level Map

| Path | Purpose | Evidence |
|------|---------|----------|
| `main.py` | 主线唯一入口：采集/登录/守护进程三种模式 | `main.py:59-105` |
| `config/` | 两级配置（.env 密钥 + config.yaml 参数） | `config/settings.py` |
| `models/` | Pydantic 数据模型（Post、ScrapeTarget、RunLog） | `models/schemas.py` |
| `browser/` | Playwright 生命周期 + 抖音登录 + 反检测 | `browser/manager.py` |
| `extractors/` | 抖音 API 拦截与用户/话题页采集 | `extractors/interceptor.py` |
| `transcriber/` | 视频下载、音频提取、Whisper/火山 ASR、文案精炼 | `transcriber/volc_asr.py` |
| `pipeline/` | 流程编排（Orchestrator）与去重 | `pipeline/orchestrator.py` |
| `storage/` | SQLite 连接、建表、Repository CRUD | `storage/repository.py` |
| `feishu/` | 飞书认证、多维表格（目标管理）、文档（日报输出） | `feishu/document.py` |
| `content_engine/` | AI 文案整理 + 过改质检 | `content_engine/pipeline.py` |
| `ai/` | DeepSeek API 封装 + Prompt 加载 | `ai/provider.py` |
| `utils/` | 统一异常定义 | `utils/exceptions.py` |
| `prompts/` | 外部化 Markdown Prompt（rewrite.md） | `ai/prompt_loader.py` |
| `scripts/` | PowerShell：安装、运行、注册定时任务 | `scripts/register_task.ps1` |
| `data/` | 运行时数据：SQLite、抖音 Cookie、临时视频 | `data/wenan_catch.db` |
| `cache/` | 视频/音频下载缓存（当前残留大视频文件） | `cache/videos/*.mp4` |
| `logs/` | loguru 按天轮转日志 | `main.py:48-56` |
| `pdf2ppt/` | 成熟流水线：竖版漫画 PDF → 16:9 教学 PPT（5 阶段） | `pdf2ppt/README.md` |
| `docx2ppt/` | 新流水线：预测案例 docx → PPT（parse/deck/chart） | `docx2ppt/parse.py` |
| `81work/` | 《81格局龙渊》工作区：用户配图、PPT 版本、验证脚本 | `81work/verify_ppt.py` |
| `comic_doubao/`、`comic_smartcrop/`、`comic_images/` | 豆包 AI 生图、智能裁剪、漫画配图库 | 目录内 p00x_c00.png 文件 |
| `.claude/` | 本地 skill：kami（排版）、pdf-to-ppt（自研流水线） | `.claude/skills/*/SKILL.md` |
| `_user_images/` | 用户手工裁剪的配图库（PPT 用） | 目录内 slide*.png |
| 根目录 `*.py`（60+ 个） | 一次性/阶段性脚本：build_*.py、verify_*.py、check_*.py、test_*.py | `build_qimen_html.py`、`final_verify.py` 等 |
| 根目录大文件 | 产物与中间件：`*.pptx`、`*.pdf`、`*.html`、`base64_map.json`(3.7MB)、`qimen_cases.json`(152KB) | 根目录列表 |

### 2) Entry Points

- 主线运行时入口：`main.py`（argparse 选择 once/login/daemon 模式，`main.py:59-105`）
- 内容制作线：**无统一入口**。每条流水线独立运行：
  - PDF→PPT：`pdf2ppt/run_pipeline.py "漫画.pdf" [--from N]`
  - DOCX→JSON→HTML：`extract_qimen.py` → `build_qimen_html.py`
  - DOCX→PPTX：`docx2ppt/parse.py` → `docx2ppt/deck.py`（81work 验证脚本驱动）
- 入口选择方式：命令行参数（主线）；手工按顺序跑脚本（内容线）
- 定时入口：Windows 任务计划调用 `scripts/run.ps1`（注册脚本 `scripts/register_task.ps1`）

### 3) Module Boundaries

| Boundary | 职责 | 禁止 |
|----------|------|------|
| `browser/` | 浏览器生命周期、Cookie、登录、反检测、页面导航 | 不解析业务数据（`browser/manager.py` docstring） |
| `extractors/` | API 拦截 + 提取 Post 数据 | 不做去重/存储 |
| `pipeline/orchestrator.py` | 流程编排：目标→采集→ASR→AI→飞书 | 不直接写 SQL、不管浏览器细节（docstring 明示） |
| `storage/repository.py` | 唯一 CRUD 层 | 业务层禁止直接写 SQL（docstring 明示） |
| `transcriber/` | 下载→音频→ASR→精炼 | 不做内容改写（改写归 content_engine） |
| `content_engine/` | AI 整理 + 过改检测 | 不碰浏览器/存储 |
| `feishu/` | 飞书 API 全部交互 | 不承载业务判断 |
| `ai/` | DeepSeek 调用 + Prompt 加载 | Prompt 禁止硬编码在业务代码（`ai/prompt_loader.py` docstring） |
| `docx2ppt/` vs `pdf2ppt/` | 各自独立的转换流水线 | 二者**没有共享代码**（重复造轮子风险，见 CONCERNS） |

### 4) Naming and Organization Rules

- 文件命名：snake_case（`user_extractor.py`、`build_qimen_html.py`）；根目录脚本多为任务动词前缀（build_/verify_/check_/extract_/test_）
- 目录组织：主线按**层**（browser/extractors/storage/feishu）；内容线按**工作区**（81work）+ 流水线（pdf2ppt/docx2ppt）
- 导入约定：绝对导入（`from config import settings`）；`main.py:22-23` 手工 `sys.path.insert` 项目根；部分脚本（`81work/verify_ppt.py:3`）同样手工插路径
- 无 import alias（除惯用 `from docx.table import Table` 等库级导入）

### 5) Evidence

- `main.py`
- `docs/codebase/.codebase-scan.txt`（DIRECTORY TREE / ENTRY POINTS 段）
- `pipeline/orchestrator.py:1-13`、`storage/repository.py:1-6`、`ai/prompt_loader.py:1-7`
- `pdf2ppt/README.md`、`docx2ppt/parse.py`
- 根目录文件清单（`glob` 结果）
