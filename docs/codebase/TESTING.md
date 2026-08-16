# Testing Patterns 测试现状

> **本项目没有正式测试体系**：无测试框架、无测试目录、无 CI（scan 三段均为 No）。主线依赖人工验证 + 运行日志；内容制作线发展出"独立重算验证脚本"模式。

## Core Sections (Required)

### 1) Test Stack and Commands

- 主要测试框架：**无**（无 pytest/unittest 配置，requirements.txt 无测试依赖）
- 断言/模拟工具：无专用工具；验证脚本用裸 `assert`/print 对比
- Commands：

```bash
# 不存在标准测试命令。可用的“验证”类命令：
python final_verify.py          # 排盘规则独立重算，与 JSON 提取结果逐格比对
python validate_qimen.py        # 排盘表结构验证（八神/八门唯一性）
python verify_dipan.py          # 地盘干重算校验（最强校验）
python 81work/verify_ppt.py     # PPT 正文逐字校验 + 参数值校验 + 溢出预检
python 81work/audit_chart.py    # PPT 排盘页几何审计
powershell -File 81work/detect_overflow.ps1   # PowerPoint COM 真实文本溢出检测
```

### 2) Test Layout

- 测试文件位置：无固定位置。根目录 `test_*.py`（`test_asr.py`、`test_one_img.py` 等）是**一次性调试脚本**，不是测试套件
- 命名惯例：验证脚本动词前缀 `verify_*` / `validate_*` / `audit_*` / `check_*`，散落根目录与 `81work/`
- Setup 文件：无

### 3) Test Scope Matrix

| Scope | Covered? | Typical target | Notes |
|-------|----------|----------------|-------|
| 单元测试 | 否 | — | 无任何单元测试文件 |
| 集成测试 | 部分（手工） | 主线靠 `--dry-run` 与真实运行；`test_asr.py` 试用火山 ASR | `main.py:99-103`（dry-run 参数） |
| E2E | 部分（手工） | 主线每日定时任务即 E2E；内容线验证脚本覆盖"数据正确性"E2E | `final_verify.py` 等 |
| 内容正确性验证 | 是（内容线特色） | 排盘九宫数据、PPT 文本逐字 | 独立重算比对模式，见下 |

### 4) Mocking and Isolation Strategy

- 模拟策略：无 mock。隔离靠**纯函数化重算**——验证脚本不依赖被测代码的提取逻辑，而是按领域规则（遁局→地盘干公式、八门唯一性）独立计算后比对（`final_verify.py:14-30`）
- 隔离保证：无（验证脚本直接读 JSON/PPTX 产物文件）
- 常见失效模式：源文档本身有错（如"天任 星值使"错字、表16 乾6宫 休→生）时，验证脚本会误报提取 bug——已用"源数据异常 vs 提取bug"区分（`validate_qimen.py:1`、`extract_qimen.py:152-156`）

### 5) Coverage and Quality Signals

- 覆盖率工具 + 阈值：无
- 当前报告覆盖率：无 [TODO]
- 已知缺口/薄弱区：
  1. 主线采集/ASR/飞书链路无任何自动化测试（浏览器行为与外部 API 依赖重）
  2. 内容线验证覆盖数据正确性，但**不覆盖布局美观性**（溢出检测是估算公式，最终靠 PowerPoint COM 实测 `detect_overflow.ps1`）

### 6) Evidence

- `requirements.txt`（无测试依赖）
- `docs/codebase/.codebase-scan.txt`（PERFORMANCE & TESTING 段：No performance testing configs detected）
- `final_verify.py`、`81work/verify_ppt.py`、`81work/detect_overflow.ps1`
- 根目录 `test_asr.py`（调试脚本样本）
