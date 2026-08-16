"""
统一 PPT 字体和字号，确保文字不超出页面
- 只改文本（字体、字号）
- 不动图片、不动布局
"""
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.oxml.ns import qn
from lxml import etree
import math

UNIFORM_FONT = "微软雅黑"
SLIDE_W = 12188952  # 13.33in
SLIDE_H = 6858000   # 7.5in


def set_run_font(run, font_name, size_pt, bold=None):
    """设置 run 字体"""
    if font_name:
        run.font.name = font_name
        # 设置东亚字体（中文关键）
        rPr = run._r.get_or_add_rPr()
        ea = rPr.find(qn('a:ea'))
        if ea is None:
            ea = etree.SubElement(rPr, qn('a:ea'))
        ea.set('typeface', font_name)
    if size_pt:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold


def est_lines(text, size_pt, box_w_emu):
    """估算文字行数"""
    w_in = box_w_emu / 914400
    if w_in <= 0 or size_pt <= 0:
        return 1
    cpl = max(1, (w_in * 72) / (size_pt * 0.9))  # 中文约 0.9 倍字号宽
    lines = 0
    for seg in text.split('\n'):
        if not seg.strip():
            lines += 1
        else:
            lines += max(1, math.ceil(len(seg) / cpl))
    return lines


def est_height_emu(text, size_pt, box_w_emu, spacing=1.3):
    """估算文字高度 EMU"""
    lines = est_lines(text, size_pt, box_w_emu)
    line_h_pt = size_pt * spacing
    return int(lines * line_h_pt * 12700) + Emu(60000)


def process_text_frame(sh, snum):
    """统一单个文本框的字体字号，防溢出"""
    tf = sh.text_frame
    if not tf.text.strip():
        return

    # 文本框可用高度（不能超出页面）
    avail_h = SLIDE_H - sh.top - Emu(100000)  # 底部留白
    if avail_h <= 0:
        avail_h = sh.height

    # 判断是否为标题框：字号大或文字短
    runs = [r for p in tf.paragraphs for r in p.runs if r.text.strip()]
    if not runs:
        return

    max_pt = max((r.font.size / 12700 if r.font.size else 14) for r in runs)
    total_text = ''.join(r.text for r in runs)
    is_title = max_pt >= 18 or len(total_text) <= 15

    if is_title:
        target_pt = min(max_pt, 20)
        new_pt = target_pt
        # 标题字号足够大时，检查溢出
        needed = est_height_emu(tf.text, new_pt, sh.width)
        while needed > avail_h and new_pt > 12:
            new_pt -= 1
            needed = est_height_emu(tf.text, new_pt, sh.width)
        for r in runs:
            set_run_font(r, UNIFORM_FONT, new_pt, bold=False)
    else:
        # 正文：根据文字量选字号
        text_len = len(total_text)
        if text_len < 80:
            target_pt = 16
        elif text_len < 200:
            target_pt = 14
        elif text_len < 400:
            target_pt = 13
        else:
            target_pt = 12

        # 检查是否溢出，溢出则缩小
        new_pt = target_pt
        needed = est_height_emu(tf.text, new_pt, sh.width)
        while needed > avail_h and new_pt > 9:
            new_pt -= 0.5
            needed = est_height_emu(tf.text, new_pt, sh.width)

        for r in runs:
            set_run_font(r, UNIFORM_FONT, new_pt, bold=False)


def main():
    prs = Presentation(r'e:\wenan catch\output_final.pptx')
    processed = 0
    for snum, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if sh.has_text_frame:
                process_text_frame(sh, snum)
                processed += 1

    prs.save(r'e:\wenan catch\output_final.pptx')
    print(f"Unified fonts across {processed} text frames")
    print(f"Font: {UNIFORM_FONT}")


if __name__ == "__main__":
    main()
