"""
生成 PPT slide ↔ PDF 页绑定文件 slide_pdf_binding.json

绑定方法：用每页 PPT 首句（>12字）在 PDF 页文本中匹配。
输出每页的：pdf_page、pdf 完整文字（含坐标/text_type）、ppt 当前文字。
"""
import json
import re
from pptx import Presentation

PDF_JSON = r'C:\Users\Kimura\Desktop\待处理\comic_page_models.json'
PPTX = r'e:\wenan catch\output_final.pptx'
OUTPUT = r'e:\wenan catch\slide_pdf_binding.json'

# ── 加载 PDF 提取数据 ──
pages = json.load(open(PDF_JSON, 'r', encoding='utf-8'))

def pdf_search_text(page):
    """PDF 页的全部文本（用于匹配）"""
    return '\n'.join(
        t['text'].strip() for t in page.get('text_items', [])
        if t.get('text_type') != 'page_number' and t['text'].strip()
    )

def pdf_full_items(page):
    """PDF 页的全部文字项（含坐标和类型）"""
    return [
        {
            "text": t['text'].strip(),
            "bbox": t.get('bbox', []),
            "font_size": t.get('font_size', 0),
            "text_type": t.get('text_type', 'body'),
        }
        for t in page.get('text_items', [])
        if t['text'].strip()
    ]

# ── 加载 PPT ──
prs = Presentation(PPTX)

def ppt_first_text(slide):
    """取 PPT 页首个长句用于匹配"""
    for sh in slide.shapes:
        if sh.has_text_frame:
            for line in sh.text_frame.text.split('\n'):
                line = line.strip()
                # 跳过页码/页眉（如"第X页"、书名）
                if len(line) > 12 and not re.match(r'^第\d+页$', line):
                    return line
    return ''

def ppt_all_text(slide):
    """PPT 页全部文本"""
    return '\n'.join(
        sh.text_frame.text.strip()
        for sh in slide.shapes
        if sh.has_text_frame and sh.text_frame.text.strip()
    )

# ── 建立绑定 ──
binding = {}
for snum, slide in enumerate(prs.slides, 1):
    first = ppt_first_text(slide)
    pdf_page = None
    if first:
        key = first[:20]
        for p in pages:
            if key in pdf_search_text(p):
                pdf_page = p['page_num']
                break

    entry = {
        "pdf_page": pdf_page,
        "ppt_first_text": first,
    }
    if pdf_page:
        p = pages[pdf_page - 1]
        entry["pdf_type"] = p.get('page_type', '')
        entry["pdf_text"] = pdf_search_text(p)
        entry["pdf_text_with_pos"] = pdf_full_items(p)
    entry["ppt_text"] = ppt_all_text(slide)
    binding[f"slide_{snum}"] = entry

# ── 保存 ──
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(binding, f, ensure_ascii=False, indent=2)

# ── 统计 ──
matched = sum(1 for e in binding.values() if e['pdf_page'])
total = len(binding)
print(f"绑定完成: {matched} / {total} 页成功匹配")
print(f"未匹配页: {[k for k, v in binding.items() if not v['pdf_page']]}")
print(f"输出: {OUTPUT} ({__import__('os').path.getsize(OUTPUT)/1024:.0f} KB)")

# 抽查
print("\n=== 抽查前 10 页 ===")
for snum in range(1, 11):
    e = binding[f"slide_{snum}"]
    print(f"  Slide {snum:3d} → PDF {e['pdf_page']} | {e['ppt_first_text'][:40]}")
