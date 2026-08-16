# 抖音文案采集系统

自动采集指定抖音用户和话题的视频文案，通过 Whisper 语音转文字确保即使视频没有字幕也能获取完整口播文案，最终生成飞书日报文档。

## 功能特性

- 🎯 **多目标追踪** — 支持追踪多个抖音用户和话题，通过飞书多维表格管理
- 🎤 **语音转文字** — 基于 OpenAI Whisper，视频没有字幕也能提取完整口播文案
- 📊 **飞书日报** — 每天自动生成结构化日报文档，按用户/话题分区展示
- 🤖 **全自动运行** — Windows 定时任务，每日自动采集
- 🛡️ **反检测机制** — 模拟真实用户行为，降低被封风险
- 💾 **增量去重** — 只采集新视频，避免重复

## 系统架构

```
┌─────────────────────────────────────────────────┐
│ 飞书多维表格 (管理目标用户/话题)                    │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ Playwright 浏览器自动化                           │
│ ├─ 加载 Cookie → 访问目标页面                     │
│ ├─ 拦截 API 响应 → 提取视频元数据                  │
│ ├─ 页面已有文案？→ 直接提取                        │
│ └─ 没有文案？→ 下载视频 → Whisper 语音转文字       │
└────────────────────┬────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────┐
│ SQLite 去重存储 → 飞书日报文档                     │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Python 3.10+
- NVIDIA 显卡（推荐，用于 Whisper GPU 加速）
- ffmpeg（用于视频音频提取）

### 一键安装

```powershell
# 1. 运行安装脚本（创建虚拟环境、安装依赖、安装浏览器）
.\scripts\setup.ps1

# 2. 安装 ffmpeg（如果还没有）
#    下载 https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
#    解压后把 bin 目录加入系统 PATH
```

### 抖音登录

```powershell
# 首次运行需要扫码登录
python main.py --mode login

# 会弹出浏览器窗口，用抖音 App 扫码
# 登录成功后 Cookie 会自动保存
```

### 配置飞书

#### 第一步：创建飞书自建应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建应用」→「企业自建应用」
3. 应用名称：`抖音文案采集系统`
4. 应用描述：`自动采集抖音视频文案并生成日报`

#### 第二步：配置权限

在应用的管理页面，进入「权限管理」，添加以下权限：

| 权限 | 说明 |
|------|------|
| `bitable:app` | 读取多维表格（获取目标列表） |
| `docx:document` | 读写文档（创建日报） |
| `drive:drive` | 云文档管理（移动文档到文件夹） |
| `contact:contact.employee:readonly` | 读取成员信息（可选） |

#### 第三步：获取凭证

1. 进入「凭证与基础信息」页面
2. 复制 `App ID` 和 `App Secret`
3. 填入项目根目录的 `.env` 文件：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 第四步：发布应用

1. 进入「版本管理与发布」
2. 创建版本，填写版本号 `1.0.0`
3. 点击「提交发布」
4. 联系飞书管理员审批

#### 第五步：创建多维表格（管理目标）

1. 在飞书文档中创建一个多维表格，命名为 `抖音采集目标管理`
2. 添加以下列：

| 字段名 | 字段类型 | 说明 |
|--------|----------|------|
| 名称 | 文本 | 目标名称，如"张三"或"生活日常" |
| 类型 | 单选 | `user` 或 `hashtag` |
| 抖音ID | 文本 | 用户的 sec_uid 或话题的 hashtag_id |
| 状态 | 单选 | `active`（启用）或 `paused`（暂停） |
| 备注 | 文本 | 可选备注 |

3. 添加你要追踪的目标
4. 复制多维表格的 URL，从中提取 `app_token`：
   - URL 格式：`https://xxx.feishu.cn/base/BITABIxxx?table=tblxxx&view=vewxxx`
   - `BITABIxxx` 就是 app_token
   - `tblxxx` 就是 table_id

5. 填入 `.env` 文件：

```env
FEISHU_BITABLE_APP_TOKEN=BITABIxxxxxxxxxxxxxxxx
FEISHU_TARGET_TABLE_ID=tblxxxxxxxxxxxxxxxx
```

#### 第六步：创建日报文件夹

1. 在飞书文档中创建一个文件夹，命名为 `抖音文案日报`
2. 进入文件夹，从 URL 中提取 `folder_token`
   - URL 格式：`https://xxx.feishu.cn/drive/folder/fldxxxxx`
   - `fldxxxxx` 就是 folder_token
3. 填入 `.env`：

```env
FEISHU_DOCUMENT_FOLDER_TOKEN=fldxxxxxxxxxxxxxxxx
```

### 运行采集

```powershell
# 测试采集（显示浏览器界面方便调试）
python main.py --mode once --no-headless

# 正式采集（无头模式，后台静默运行）
python main.py --mode once

# 试运行（不写入飞书）
python main.py --mode once --dry-run

# 跳过语音转文字（只采集页面已有文案）
python main.py --mode once --no-transcribe
```

### 设置定时任务

```powershell
# 注册每天 08:00 自动执行的定时任务
.\scripts\register_task.ps1

# 指定其他时间
.\scripts\register_task.ps1 -Time 09:30

# 删除定时任务
.\scripts\register_task.ps1 -Unregister
```

## 使用指南

### 如何获取抖音 User ID (sec_uid)

1. 打开抖音网页版：`https://www.douyin.com`
2. 进入目标用户的主页
3. 查看浏览器地址栏：
   - `https://www.douyin.com/user/MS4wLjABAAAA...`
   - `MS4wLjABAAAA...` 就是 sec_uid

### 如何获取话题 ID

1. 在抖音中搜索话题，如 `#生活日常`
2. 进入话题页面
3. 查看浏览器地址栏：
   - `https://www.douyin.com/hashtag/123456789`
   - `123456789` 就是 hashtag_id

### 如何查看运行日志

```powershell
# 日志文件位于 logs/ 目录
Get-Content logs\wenan_catch_2026-07-09.log -Tail 50
```

## 项目结构

```
e:\wenan catch\
├── main.py                       # 主入口
├── config/                       # 配置管理
│   ├── settings.py               # Pydantic 配置
│   └── config.yaml               # 非敏感配置
├── models/                       # 数据模型
│   └── schemas.py                # Post, ScrapeTarget 等
├── browser/                      # 浏览器自动化
│   ├── manager.py                # Playwright 生命周期
│   ├── login.py                  # 扫码登录
│   ├── anti_detect.py            # 反检测脚本
│   └── navigator.py              # 页面导航助手
├── extractors/                   # 数据采集
│   ├── interceptor.py            # API 拦截解析
│   ├── user_extractor.py         # 用户主页采集
│   └── hashtag_extractor.py      # 话题页采集
├── transcriber/                  # 语音转文字
│   ├── downloader.py             # 视频下载
│   ├── audio.py                  # 音频提取
│   └── stt.py                    # Whisper 语音识别
├── storage/                      # 数据存储
│   ├── schema.sql                # 数据库表结构
│   ├── database.py               # 数据库连接
│   └── repository.py             # CRUD 操作
├── feishu/                       # 飞书集成
│   ├── auth.py                   # 认证管理
│   ├── bitable.py                # 多维表格
│   ├── document.py               # 文档管理
│   └── formatter.py              # 文档内容构建
├── pipeline/                     # 流程编排
│   ├── orchestrator.py           # 总控编排器
│   └── dedup.py                  # 去重引擎
├── scripts/                      # 辅助脚本
│   ├── setup.ps1                 # 一键安装
│   ├── run.ps1                   # 手动运行
│   └── register_task.ps1         # 注册定时任务
├── data/                         # 运行时数据
│   └── cookies/                  # Cookie 文件
└── logs/                         # 运行日志
```

## 常见问题

### Q: 提示"登录状态失效"怎么办？

```powershell
# 重新扫码登录
python main.py --mode login
```

### Q: Whisper 识别效果不好？

- 确保使用 medium 或 large-v3 模型（在 config.yaml 中修改 `transcriber.model_size`）
- 确保视频音频清晰，背景噪音小
- 首次运行会下载模型文件，需要网络连接

### Q: 飞书文档为空？

- 检查飞书 API 权限是否已配置
- 检查 `.env` 中的 `FEISHU_DOCUMENT_FOLDER_TOKEN` 是否正确
- 运行 `--dry-run` 模式观察日志输出

### Q: 报错 "No module named 'lark'"？

```powershell
# 飞书 SDK 可选，不影响核心采集功能
# 如需飞书集成，执行：
pip install lark
```

### Q: ffmpeg 找不到？

1. 下载 ffmpeg: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. 解压到 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 添加到系统 PATH
4. 重启终端

## 技术栈

| 用途 | 库/工具 |
|------|---------|
| 浏览器自动化 | Playwright |
| 语音识别 | OpenAI Whisper |
| 音频处理 | ffmpeg |
| 飞书 API | Lark SDK / httpx |
| 数据验证 | Pydantic |
| 数据存储 | SQLite |
| 日志 | Loguru |
| 定时任务 | Windows Task Scheduler |
