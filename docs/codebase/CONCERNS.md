# Codebase Concerns 风险与关注点

## Core Sections (Required)

### 1) Top Risks (Prioritized)

| Severity | Concern | Evidence | Impact | Suggested action |
|----------|---------|----------|--------|------------------|
| 高 | **无版本控制**（不是 git 仓库，无任何 VCS） | scan：Not a git repository；目录内无 `.git` | 任何误改/误删不可回滚；产物靠手工文件名备份（`output_final_backup2.pptx`） | `git init` + 首次提交 + 合理 .gitignore（已有 `.gitignore` 草案） |
| 高 | **`.env` 含真实密钥且无 VCS 保护** | `.env` 在根目录（飞书/火山/DeepSeek 全套 key） | 一旦误分享/误打包目录即泄露全部凭证 | git init 前确认 `.gitignore` 覆盖 `.env`；建议密钥轮换计划 [ASK USER] |
| 中 | 根目录脚本丛林 + 大文件混放 | 根目录 60+ 一次性 .py；`base64_map.json` 3.7MB、多个 40MB 级 .pptx | 新接手者无法分辨"最终产物 vs 中间物 vs 备份" | 归档：`scripts_archive/` 或按任务建目录；产物命名规范 |
| 中 | 主线已 3 周未运行（2026-07-15 后无日志），抖音 Cookie 大概率失效 | `logs/wenan_catch_2026-07-15.log` 为最新；Cookie 文件 7/8 生成 | 定时任务仍在跑则每日静默失败；恢复需人工扫码 | 确认任务计划状态 [ASK USER]；跑一次 `--dry-run` 验证链路 |
| 中 | 内容制作线依赖无版本记录 | requirements.txt 缺 python-pptx/PyMuPDF/python-docx/Pillow | 换机无法复现环境 | 补 requirements 或生成 requirements-full.txt |

### 2) Technical Debt

| Debt item | Why it exists | Where | Risk if ignored | Suggested fix |
|-----------|---------------|-------|-----------------|---------------|
| README 与代码脱节 | README 描述 V1 架构（interceptor 未列、content_engine 五模块），实际 V1 模块已删（pycache 残留 classifier/analyzer/template_manager/style_manager） | `README.md` vs `content_engine/__pycache__/` | 误导接手者 | 更新 README 或补模块现状说明 |
| 双流水线重复代码 | pdf2ppt 与 docx2ppt 独立开发（PDF 源 vs DOCX 源） | `pdf2ppt/` + `docx2ppt/` | 风格/修复需双份维护 | 提取共享的 Kami 样式/排版层 |
| 硬编码绝对路径 | 脚本直接写死机器路径 | `extract_qimen.py:9`、`81work/verify_ppt.py:7-8` | 换机即断 | 参数化或读配置 |
| 死代码残留 | 无效循环、pass 分支 | `extract_qimen.py:202-209` | 混淆理解 | 清理 |
| 配置与代码脱节 | `config.yaml` 有 `douyin.max_new_per_target: 3`，但 `config/settings.py` 映射表未收录，orchestrator 里硬编码 `MAX_NEW_PER_TARGET = 3`（`pipeline/orchestrator.py:238`） | `config/config.yaml:29` vs `config/settings.py:116-153` | 改配置不生效，两处需同步 | 把该项加入 settings 映射或删除 yaml 冗余项 |
| 缓存清理失效 | `_cleanup_cache` 已实现但 `cache/videos/` 残留 43-95MB 视频 | `pipeline/orchestrator.py:462-477` vs `cache/videos/` | 磁盘膨胀 | 排查清理条件（可能只清 data/temp_videos） |

### 3) Security Concerns

| Risk | OWASP category | Evidence | Current mitigation | Gap |
|------|----------------|----------|--------------------|-----|
| 凭证明文存磁盘 | A02（加密失效） | `.env` 明文 | 无 VCS（未外泄） | git init 时必须排除；无轮换 |
| 抖音 Cookie 明文 | A02 | `data/cookies/douyin_cookies.json` 明文 | 本机单文件 | 无过期自动提醒（运行时报错才知） |
| 采集行为合规 | N/A（平台条款） | 反检测+随机延时（`config/settings.py:56-65`） | 已有反检测 | 账号风控为长期风险 [ASK USER] |
| 内容线外部输入 | A03（注入类） | docx/PDF 解析直接 trust 源内容（`docx2ppt/parse.py`） | 本地文件场景 | 低风险（无远程输入） |

### 4) Performance and Scaling Concerns

| Concern | Evidence | Current symptom | Scaling risk | Suggested improvement |
|---------|----------|-----------------|-------------|-----------------------|
| 采集串行 | Orchestrator 逐目标 for 循环 + 5-8s 延时（`pipeline/orchestrator.py:98-107`） | 目标多时耗时长 | 目标数增长线性变慢 | 目标少时不必动；多目标可限流并行 |
| 每日每目标限 3 条 | `MAX_NEW_PER_TARGET = 3`（`pipeline/orchestrator.py:238`） | 新视频超 3 条被丢弃（不排队） | 内容积累慢 | [ASK USER] 是否仍适用 |
| ASR/AI 串行 | 每账号 posts 逐个处理（`pipeline/orchestrator.py:287,412`） | 单账号多视频时慢 | 线性 | 批量 API 或并发（需注意配额） |
| 本地模型重 | Whisper tiny 需 ~1GB VRAM（`transcriber/stt.py` docstring） | 备用引擎 | 仅当切换回 Whisper 时 | 当前默认火山 ASR，无影响 |

### 5) Fragile/High-Churn Areas

| Area | Why fragile | Churn signal | Safe change strategy |
|------|-------------|-------------|----------------------|
| `extract_qimen.py` + 验证脚本群 | 对源 docx 格式高度耦合（嵌套表格八神、表16 人工修正 hardcode） | 8/5 当天 10+ 个验证/修正脚本密集迭代 | 改前跑 `final_verify.py` 回归；修正项集中在 `extract_qimen.py:152-156` |
| 抖音反爬链路（browser/extractors） | 页面结构/API 变动即失效 | 7/8-7/15 密集开发后冻结 | 改前 `--no-headless` 观察；保持随机延时参数 |
| `pdf2ppt/clean.py` LLM 清理 | 依赖 workflow 外部执行，rule/llm 双模式质量差异大（README:75-77 明示 rule 不可用于成品） | 7/31 迭代 | 只允许 llm 模式产出正式版 |
| Kami 样式（HTML/PPT 双实现） | 配色/字号常量散落各脚本（`build_qimen_html.py` CSS、`docx2ppt/deck.py`、`pdf2ppt/build_ppt.py` 各一份） | 多次微调（羊皮纸/墨蓝体系） | 样式改动需三处同步；长期应抽共享模块 |

### 6) `[ASK USER]` Questions

1. [ASK USER] 主线（抖音文案采集）是否仍要持续运营？Windows 定时任务现在还在跑吗？需要现在恢复（重新扫码登录）吗？
2. [ASK USER] 当前最高优先级是否为奇门遁甲课程（8/5 的预测案例 PPT/HTML）？下一步是继续打磨还是交付？
3. [ASK USER] 根目录大量脚本与产物（60+ .py、多个 40MB 级 .pptx/.pdf、3.7MB base64_map.json），是否同意做一次归档整理？哪些文件是"最终版"（例如 `81work/预测案例_输出.pptx` 是否为交付物）？
4. [ASK USER] 是否要我 `git init` 建立版本控制？`.gitignore` 是否需要补充（cache/、*.pptx、docs/codebase/.codebase-scan.txt 等）？
5. [ASK USER] `VOLC_ARK_API_KEY` 的用途（豆包生图？）与 comic_doubao 的生成流程是什么？代码中未见调用。
6. [ASK USER] 内容线是否还有下一个文档（新书/新课程）要转换？pdf2ppt 与 docx2ppt 是否需要合并统一？

### 7) Evidence

- `docs/codebase/.codebase-scan.txt`（GIT RECENT COMMITS / CODE METRICS / CI/CD 段）
- 根目录文件清单与 `logs/` 最新日志时间
- `pipeline/orchestrator.py:238,462-477`
- `README.md` vs `content_engine/__pycache__/`
- `.env` 键名、`.gitignore`
