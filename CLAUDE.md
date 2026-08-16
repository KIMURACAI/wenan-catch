# 项目说明（CLAUDE.md）

> 本文件由 codebase-onboarding skill 生成于 2026-08-06，基于 docs/codebase/ 的 7 份知识文档。权威细节见 `docs/codebase/`。

## 项目是什么

工作目录 `E:\wenan catch` 包含两代工作：

1. **抖音文案采集系统**（主线，Python）—— 自动采集抖音用户/话题的口播文案：Playwright 采集 → 火山 ASR 转写 → DeepSeek 润色 → 飞书日报。入口 `main.py`，最后一次运行 2026-07-15。
2. **国学课程内容制作**（2026-07-20 至今，当前重心）—— 风水/奇门遁甲课程的 HTML/PDF/PPT 制作：`pdf2ppt/`（漫画 PDF→PPT 流水线）、`docx2ppt/`（docx→PPT 流水线）、`81work/`（81格局龙渊与预测案例工作区）、根目录一次性脚本群。

## Tech Stack

- Python 3.11.9 + pip（`requirements.txt`）
- 主线：playwright / lark(飞书) / httpx / pydantic(-settings) / loguru / 火山 BigModel ASR / DeepSeek API
- 内容线：python-pptx / PyMuPDF / python-docx / Pillow（**未写入 requirements.txt**）
- SQLite（`data/wenan_catch.db`）；无 Docker、无 CI、**无 git**、无测试框架

## Code Style

- 文件/函数 snake_case，类 PascalCase，常量 UPPER_SNAKE，私有方法 `_` 前缀
- 每个模块首行中文 docstring，写明"负责什么 / 不做什么"
- 日志只用 loguru，中文消息 + emoji 状态（✅/❌）；主入口 `main.py:setup_logging` 配置按天轮转
- 异常统一定义在 `utils/exceptions.py`；Orchestrator 逐目标兜底不中断
- Prompt 放 `prompts/` 与 `content_engine/prompts/`，禁止硬编码
- 无 linter/formatter 配置；手工保持 4 空格缩进
- 内容线原则：**源文字一字不改**（只做格式整理）；验证靠独立重算比对（`verify_*/validate_*/audit_*` 脚本）

## Testing

- 无正式测试体系。调试脚本（`test_*.py`）不是测试套件
- 内容线验证命令：
  - `python final_verify.py`（排盘规则重算比对）
  - `python 81work/verify_ppt.py`（PPT 正文逐字 + 溢出预检）
  - `powershell -File 81work/detect_overflow.ps1`（PowerPoint COM 实测溢出）
- 改动内容线后，先跑对应验证脚本再交付

## Build & Run

```bash
# 主线
python main.py --mode once [--no-transcribe] [--ai-refine] [--dry-run]
python main.py --mode login          # 抖音 Cookie 过期时重新扫码
.\scripts\register_task.ps1          # 注册/取消每日定时任务

# 内容线（无统一入口，按需）
python pdf2ppt/run_pipeline.py "漫画.pdf" [--from N]
python extract_qimen.py && python build_qimen_html.py
python 81work/verify_ppt.py
```

## Project Structure

```
main.py                 主线入口（once/login/daemon）
config/ models/         配置（.env+yaml 两级）与 Pydantic 模型
browser/ extractors/    Playwright 采集 + 抖音 API 拦截
transcriber/            下载→音频→火山ASR→文案精炼
pipeline/               Orchestrator 编排 + 去重
storage/                SQLite + Repository（唯一 CRUD）
content_engine/ ai/     DeepSeek 整理 + 过改检测
feishu/                 认证/多维表格/日报文档
pdf2ppt/ docx2ppt/      两条文档→PPT 流水线（不共享代码）
81work/                 81格局龙渊与预测案例工作区（用户配图+验证）
docs/codebase/          本知识库（7 份文档，接手必读）
.claude/skills/         本地 skill：kami（排版）、pdf-to-ppt（自研）
```

## Conventions / 注意

- **不是 git 仓库**。改重要产物前手工备份（现有惯例 `_backup` 后缀）；如需 git init 先确认 `.gitignore` 补充 `cache/`、`*.pptx`、`docs/codebase/.codebase-scan.txt`
- 密钥全在 `.env`（明文，勿提交/分享）
- 配置两级：`.env`（密钥）> `config/config.yaml`（参数）> settings.py 默认值；注意 yaml 与代码存在脱节项（如 `max_new_per_target`）
- 内容线脚本普遍硬编码绝对路径 `e:\wenan catch\`，换机需改
- 排盘数据正确性极高敏感：表16 有人工规则修正（`extract_qimen.py:152-156`），改动后必须跑 `final_verify.py`
