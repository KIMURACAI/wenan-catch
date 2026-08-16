# PDF → 横版 PPT 完整流水线

将竖版漫画/图文 PDF 转为横版 16:9 教学 PPT，自动提取文字、清理漫画对话、重排分段、缩放图片排版。

## 总览

```
原版PDF ─→ [1.提取] ─→ comic_page_models.json (文字+坐标+类型)
               │
               ├─→ [2.建PPT] ─→ output_raw.pptx (左图右文初步版)
               │
               ├─→ [3.绑定] ─→ slide_pdf_binding.json (PPT↔PDF对应)
               │
               ├─→ [4.清理重排] ─→ cleaned_paragraphs.json (删对话+拼正文)
               │
               └─→ [5.应用+排版] ─→ output_final.pptx (最终版)
```

## 快速开始

```bash
# 一键全流程（从 PDF 到最终 PPT）
python pdf2ppt/run_pipeline.py "漫画.pdf"

# 分阶段执行（可断点续跑）
python pdf2ppt/run_pipeline.py "漫画.pdf" --from 1   # 提取
python pdf2ppt/run_pipeline.py "漫画.pdf" --from 3   # 绑定
python pdf2ppt/run_pipeline.py "漫画.pdf" --from 5   # 只做排版
```

## 依赖

- PyMuPDF (fitz)
- python-pptx
- Pillow
- 可选：`deepseek` 或 LLM API 用于智能清理（Stage 4）

## 阶段说明

### Stage 1 · 提取 (extract.py)
用 PyMuPDF 从 PDF 提取每页文字块（含坐标 bbox、字号、text_type）、嵌入图片、页面类型。
输出：`comic_page_models.json`

### Stage 2 · 初步建 PPT (build_ppt.py)
用提取的数据生成 16:9 PPT：Kami 风格（羊皮纸底+墨蓝），左图右文布局。
输出：`output_raw.pptx`

### Stage 3 · 绑定 (binding.py)
通过文本匹配建立 PPT 每页 ↔ PDF 原始页的对应关系。
输出：`slide_pdf_binding.json`

### Stage 4 · 清理+重排 (clean.py)
基于绑定数据，逐页：
- 删除漫画人物对话（口语第一人称台词）
- 删除罗盘/图注标注碎片
- 按 PDF 坐标把断行拼回完整段落
输出：`cleaned_paragraphs.json`

### Stage 5 · 应用+排版 (layout.py)
- 把清理后的段落写回 PPT 主文本框（字号自适应防溢出）
- 拉伸图片填满左半页（保持宽高比不裁剪）
- 多图页网格排列、图表页放大
输出：`output_final.pptx`

## 自定义图片

如果你的图是自己裁好的（不在 PDF 里），把图片放到 `_user_images/`，命名为
`slide001_img01.png`…（slide 编号 + 该页第几张图），Stage 2 会优先使用这些图。

> 注意：Stage 2 每页一个 slide（封面占 slide 1），所以 PDF 第 N 页 → slide N+1 → 图名 `slide{NNN}_img*.png`。
> 多图页用 `slide007_img01.png`、`slide007_img02.png` 顺序命名。

## 清理模式选择

> ⚠️ **已诊断确认**：`rule` 模式质量不足，**必须用 `llm` 模式**才能达到正式版效果。
> rule 用关键词判断，会漏删无标点图注（"中医""数学"）、把表格糊成一坨、标题粘进正文。
> llm 用语义判断，正确删除漫画对话/罗盘标注、按编号项分段、保留表格单元格。

| 模式 | 命令 | 质量 | 备注 |
|------|------|------|------|
| **llm（标准）** | `--clean-mode llm` | 高 | 与正式版相同，需跑 workflow |
| rule（实验） | `--clean-mode rule` | 低 | 仅无 API 时兜底，勿用于成品 |

LLM 模式流程：
```bash
# 1. 生成批次（seg_batches/part_N.json）
python -m pdf2ppt.run_pipeline "漫画.pdf" --from 4 --clean-mode llm
# 2. 用 Workflow 跑 pdf2ppt/workflow_clean.js（args 传批次信息）
# 3. 合并结果
python pdf2ppt/merge_workflow.py <journal.jsonl> -o <workdir>/cleaned_paragraphs.json
# 4. 继续 Stage 5
python -m pdf2ppt.run_pipeline "漫画.pdf" --from 5
```

**已验证质量**（154 页漫画 PDF）：
- 与人工审核版逐页对比：86% 完全一致，其余仅分段粒度差异（无乱序、无误删正文）
- 编号项（"1、""（1）"）独立分段、表格单元格（"上元""一运1864-1883水"）独立分段

## 文件清单

| 文件 | 作用 |
|------|------|
| `run_pipeline.py` | 主控脚本，串联所有阶段 |
| `extract.py` | Stage 1: PDF 内容提取 |
| `build_ppt.py` | Stage 2: 初步 PPT 生成 |
| `binding.py` | Stage 3: PPT↔PDF 绑定 |
| `clean.py` | Stage 4: 清理对话 + 重排正文（rule/llm 双模式） |
| `workflow_clean.js` | Stage 4 LLM 模式用的 workflow |
| `merge_workflow.py` | 合并 workflow 结果 |
| `layout.py` | Stage 5: 应用文字 + 图片排版 |
| `README.md` | 本文档 |

## 实际使用经验

这套流水线在《中国传统风水学现代应用经典 漫画.pdf》(154页) 上验证过完整链路。要点：

1. **图片是核心**：最终效果依赖用户裁切的配图库。PDF 内嵌图偏小，建议先用
   `extract_pdf_images.py` 导出，用户手动裁切后放入 `_user_images/`。
2. **LLM 清理更准**：rule 模式对"短句正文"可能误判，漫画对话多的书建议用 LLM 模式。
3. **页面数差异**：Stage 2 生成的页数 ≈ PDF 页数+1（封面）。若最终版经过人工
   合并短页（154→151），stage 编号会偏移，绑定阶段会重新对齐，不影响正确性。
4. **断点续跑**：中间 JSON 全部保留，改某个阶段后 `--from N` 续跑即可。
5. **断行拼接**：PDF 正文按行提取，`clean.py` 用"行尾无句号则续接"规则拼回完整段落，
   避免 PPT 里一段话被拆成多行。
