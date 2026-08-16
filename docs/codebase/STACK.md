# Technology Stack 技术栈

> 本目录包含两大块工作：①抖音文案采集系统（主线，Python 包结构）；②国学课程内容制作流水线（一次性脚本群）。
> 本文档覆盖两者实际使用的技术。

## Core Sections (Required)

### 1) Runtime Summary

| Area | Value | Evidence |
|------|-------|----------|
| 主要语言 | Python（唯一业务语言） | 扫描结果：108 个 .py 文件 / `requirements.txt` |
| 运行时 + 版本 | Python 3.11.9（本机实测） | 终端 `python --version` 输出 3.11.9 |
| 包管理器 | pip | `requirements.txt`（无 poetry/uv 信号） |
| 模块/构建系统 | 无（纯脚本 + 手工运行） | 无 pyproject.toml/setup.py/Makefile |
| 辅助语言 | PowerShell（1 个 COM 溢出检测脚本）、JavaScript（1 个 workflow） | `81work/detect_overflow.ps1`、`pdf2ppt/workflow_clean.js` |

### 2) 生产框架与依赖（requirements.txt 声明的）

| Dependency | Version | 在系统中的角色 | Evidence |
|------------|---------|----------------|----------|
| playwright | >=1.50.0 | 抖音网页采集的浏览器自动化核心 | `requirements.txt`、`browser/manager.py` |
| lark | >=1.3.0 | 飞书 SDK（文档/多维表格） | `requirements.txt`、`feishu/auth.py` |
| httpx | >=0.27.0 | 对外 HTTP 调用（飞书/DeepSeek） | `requirements.txt`、`ai/provider.py` |
| pydantic / pydantic-settings | >=2.0.0 | 数据模型 + .env 配置加载 | `requirements.txt`、`models/schemas.py`、`config/settings.py` |
| pyyaml | >=6.0 | config.yaml 非敏感配置解析 | `requirements.txt`、`config/settings.py` |
| loguru | >=0.7.0 | 全项目日志（唯一日志库） | `requirements.txt`、`main.py:setup_logging` |
| APScheduler | >=3.10.0 | 守护进程模式的定时调度（调试用） | `requirements.txt`、`main.py:run_daemon` |
| openai-whisper | >=20240930 | 本地语音转文字（备用引擎） | `requirements.txt`、`transcriber/stt.py` |
| ffmpeg-python | >=0.2.0 | 视频→音频提取 | `requirements.txt`、`transcriber/audio.py` |

### 3) 实际使用但未声明在 requirements.txt 的依赖（内容制作线）

| Dependency | 用途 | Evidence |
|------------|------|----------|
| python-pptx | 生成/校验 PPTX（docx2ppt、pdf2ppt、81work） | `docx2ppt/deck.py`、`pdf2ppt/build_ppt.py` 均 `from pptx import ...` |
| PyMuPDF (fitz) | PDF 文字/图片提取 | `pdf2ppt/extract.py`、SKILL 文档 `pdf2ppt/README.md` |
| python-docx | 解析 预测案例92-168.docx | `docx2ppt/parse.py`、`extract_qimen.py` |
| Pillow | 图片处理 | `pdf2ppt/README.md` 依赖清单 |

> 环境已装齐（本机 Python 3.11.9 可直接运行上述脚本）。

### 4) Key Commands

```bash
# ── 主线：抖音文案采集 ──
python main.py --mode once                    # 单次采集（定时任务默认）
python main.py --mode once --no-transcribe    # 跳过语音转文字
python main.py --mode once --ai-refine        # 启用 DeepSeek 润色
python main.py --mode once --dry-run          # 试运行（不写飞书）
python main.py --mode login                   # 抖音扫码登录
.\scripts\register_task.ps1                   # 注册每日 08:00 定时任务

# ── 内容制作线（各自独立，无统一入口）──
python pdf2ppt/run_pipeline.py "漫画.pdf"                     # PDF→PPT 全流程
python docx2ppt/parse.py                                      # docx 解析（看 deck 模型）
python extract_qimen.py                                       # docx → qimen_cases.json
python build_qimen_html.py                                    # json → HTML 课程
```

### 5) Environment and Config

- 配置来源：`.env`（密钥）+ `config/config.yaml`（非敏感参数）+ `config/settings.py` 默认值；两级优先级 `.env > config.yaml > 默认值`（`config/settings.py:4`）
- `.env` 实际变量：`FEISHU_APP_ID/SECRET/BITABLE_APP_TOKEN/TARGET_TABLE_ID/DOCUMENT_FOLDER_TOKEN`、`LOG_LEVEL`、`DAILY_RUN_TIME`、`VOLC_ACCESS_KEY/SECRET_KEY/APP_ID/APP_KEY`、`DEEPSEEK_API_KEY`、`VOLC_ARK_API_KEY`（全部来自 `.env` 键名列表，见 Evidence）
- `.env.template` 只包含飞书 + 运行时变量，火山/DeepSeek 变量未模板化（模板滞后于实际）
- 运行约束：Windows 本机运行；Windows 定时任务（Task Scheduler）触发；Whisper 需 ffmpeg 与（可选）NVIDIA GPU
- 内容制作线脚本中硬编码绝对路径 `e:\wenan catch\...` 和 `C:\Users\Kimura\Documents\...`（如 `extract_qimen.py:9`），跨机器不可移植

### 6) Evidence

- `requirements.txt`
- `.env` / `.env.template` / `config/config.yaml`
- `config/settings.py`
- `main.py`（argparse 运行模式定义）
- `docs/codebase/.codebase-scan.txt`（STACK DETECTION / CODE METRICS 段）
- `docx2ppt/parse.py`、`pdf2ppt/build_ppt.py`（未声明依赖的实际 import）
