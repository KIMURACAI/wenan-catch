"""
准备重分段数据：每页 PPT 当前文本 + PDF 原始正文块（按坐标排序）
输出 seg_input.json 供 workflow 分析
"""
import json
from pptx import Presentation

binding = json.load(open(r'e:\wenan catch\slide_pdf_binding.json', 'r', encoding='utf-8'))
prs = Presentation(r'e:\wenan catch\output_final.pptx')

output = []
for snum, slide in enumerate(prs.slides, 1):
    key = f"slide_{snum}"
    e = binding.get(key, {})
    pdf_page = e.get('pdf_page')

    # PPT 当前文本框（排除背景矩形）
    ppt_boxes = []
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        text = sh.text_frame.text.strip()
        if not text:
            continue
        # 跳过封面、页码单独框
        ppt_boxes.append({
            "box_type": "textbox",
            "text": text,
            "font_name": sh.text_frame.paragraphs[0].runs[0].font.name if sh.text_frame.paragraphs[0].runs else None,
            "font_size": sh.text_frame.paragraphs[0].runs[0].font.size if sh.text_frame.paragraphs[0].runs else None,
        })

    # PDF 正文块（body，按 y 排序），去掉页码/书眉/标注
    pdf_body = []
    if pdf_page:
        for item in e.get('pdf_text_with_pos', []):
            tt = item.get('text_type')
            text = item.get('text', '').strip()
            if not text:
                continue
            if text.isdigit() and len(text) <= 3:
                continue
            if text == '中国传统风水学现代应用经典':
                continue
            bbox = item.get('bbox', [])
            y = bbox[1] if len(bbox) >= 2 else 0
            pdf_body.append({
                "text": text,
                "y": y,
                "x": bbox[0] if len(bbox) >= 1 else 0,
                "text_type": tt,
            })
        pdf_body.sort(key=lambda b: (b['y'], b['x']))

    output.append({
        "slide": snum,
        "pdf_page": pdf_page,
        "ppt_boxes": ppt_boxes,
        "pdf_body_blocks": pdf_body,
    })

with open(r'e:\wenan catch\seg_input.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f"准备完成: {len(output)} 页")
print(f"输出: seg_input.json")

# 展示一页
page0 = output[5]  # slide 6
print(f"\n=== 样例 slide 6 (PDF {page0['pdf_page']}) ===")
print(f"PPT 文本框数: {len(page0['ppt_boxes'])}")
print(f"PDF 正文块数: {len(page0['pdf_body_blocks'])}")
print("PDF 正文块（按y排序）:")
for b in page0['pdf_body_blocks']:
    if b['text_type'] == 'body':
        print(f"  y={b['y']:.0f} \"{b['text']}\"")
