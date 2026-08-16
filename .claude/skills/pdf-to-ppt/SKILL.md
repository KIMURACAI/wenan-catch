---
name: pdf-to-ppt
description: "将竖版漫画/图文 PDF 转为横版 16:9 Kami 风格 PPT。提取 PDF 中的文字+配图+位置，按原版排版重排为横版幻灯片。触发词：PDF转PPT、漫画转PPT、竖版转横版、pdf to ppt、comic to slides、配图提取转PPT。"
---

# PDF 漫画/图文 → 横版 PPT 转换

将 A4 竖版 PDF（含漫画配图+文字）转为 16:9 横版 Kami 风格 PPT，保留原文排版和图文的对应关系。

## 适用场景

- 漫画/连环画 PDF → PPT 课件
- 图文混排 PDF → 横版幻灯片
- 竖版书籍 PDF → 16:9 演示文稿

## 前置条件

- PyMuPDF (fitz) 已安装
- python-pptx 已安装
- PaddleOCR 已安装（GPU 加速，支持手写/繁体/竖排）
- 火山引擎账号已配置（`.env` 中 `VOLC_ACCESS_KEY` / `VOLC_SECRET_KEY`）

## 文字提取策略（自动降级）

```
page.get_text("dict")
    │
    ├── 文字量充足 ──→ 直接使用（快、免费）
    │
    └── 文字极少/为空（扫描件/手写体）
            │
            ├── 手写/竖排/繁体 ──→ PaddleOCR（本地 GPU，离线）
            │
            └── 常规印刷体 ──→ 豆包 OCR（火山引擎云端，精度高）
```

### 判断逻辑
- 单页 `get_text("dict")` 返回字符 < 20 且页面有图 → 判定为扫描件/手写 → 走 OCR
- 用户可手动指定 `--force-ocr` 跳过文本层检测，强制走 OCR

## 工作流程

### Stage 1: 内容提取
运行 `comic_pdf_reader.py`，从 PDF 一次性提取：
- 文字块 + 坐标（`page.get_text("dict")`）
- 嵌入图片 + 坐标 + MD5 去重（`page.get_images(full=True)`）
- 矢量图检测（`page.get_drawings()`）
- 输出：`comic_page_models.json` + `comic_images/`

参数：`min_img_dim=150`（捕获小漫画角色），`dedup=True`

### Stage 2: 页面分类与编排
运行 `comic_slide_composer.py`：
- 自动分类 6 种页面类型：title_chapter / comic / text_only / diagram / full_image / mixed
- 空间分区（zone-based grouping），保留原文阅读顺序和图文的邻近关系
- 输出：`comic_slide_models.json`

### Stage 3: 生成 PPTX
运行 `build_comic_ppt.py`，使用 Kami 设计系统生成 16:9 PPT：
- 6 套横版布局模板（漫画左图右文、连环画横排、纯文字排版、图表页、全幅图、封面/章节页）
- Kami 配色：羊皮纸底 `#F5F4ED` + 墨蓝 `#1B365D`
- 字体：Source Han Serif SC

## 使用方法

```powershell
# 一键转换（使用默认参数）
python build_comic_ppt.py "PDF文件路径"

# 指定输出路径
python build_comic_ppt.py "PDF文件路径" -o "输出.pptx"

# 只提取不生成（断点续跑）
python comic_pdf_reader.py "PDF文件路径"
python comic_slide_composer.py
python build_comic_ppt.py --from-json
```

## 文件清单

| 文件 | 作用 |
|------|------|
| `comic_pdf_reader.py` | Stage 1: PDF 内容提取器 |
| `comic_slide_composer.py` | Stage 2: 页面分类+幻灯片编排 |
| `comic_layouts.py` | Stage 3a: 6 套横版布局模板 |
| `build_comic_ppt.py` | Stage 3b: 主脚本，串联所有阶段 |
| `extract_pdf_images.py` | 单独提取图片工具（仅提取图片，不做 PPT） |

## 页面分类逻辑

| 类型 | 判断条件 | 横版布局 |
|------|----------|----------|
| `title_chapter` | 大字居中、内容 < 80 字符 | Kami 封面/章节页 |
| `comic` | 2+ 张图 + 短文字 | 左图右文 (60/40) |
| `text_only` | 无图 | Kami 正文排版 |
| `diagram` | 有矢量图/表格 | 高清截图 + 注释 |
| `full_image` | 仅图无文 | 全幅图片 |
| `mixed` | 图文混合 | 图文上下/并排 |

## 注意事项

1. **自动 OCR 降级**：文本层缺失时自动切换 OCR，无需手动干预
2. **小图片捕获**：阈值 150px，确保漫画人物小图不丢失
3. **去重**：同一张图在多页出现只保留一份
4. **矢量图处理**：表格/图表等矢量图渲染为高清 PNG 嵌入
5. **断点续跑**：JSON 中间文件保留，修改分类/布局后无需重新提取

## OCR 引擎选择

| 场景 | 引擎 | 原因 |
|------|------|------|
| 有文本层（默认） | PyMuPDF | 瞬时、免费、保留坐标 |
| 手写字体 | PaddleOCR | 本地 GPU，手写模型好 |
| 竖排文字 | PaddleOCR | 支持竖排检测 |
| 繁体字 | PaddleOCR | `--lang ch` 含繁简 |
| 常规扫描件 | 豆包 OCR | 云端精度最高，火山引擎 API |
| 混合（手写+印刷） | PaddleOCR | 一次处理两种字体 |
