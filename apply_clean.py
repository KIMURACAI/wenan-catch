"""
把清理后的段落应用到 PPT：
- 每页的主正文文本框（右侧大框）替换为干净段落
- 保留所有图片、背景、页码框、分隔线
- 字号自适应防溢出
"""
import json, re, math
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.oxml.ns import qn
from lxml import etree

cleaned = json.load(open(r'e:\wenan catch\cleaned_paragraphs.json', 'r', encoding='utf-8'))
prs = Presentation('output_final.pptx')

SLIDE_W = 12188952
SLIDE_H = 6858000

# 正文文本框特征：右侧大框（left > 5in, width > 4in），含较长文字
def find_body_textbox(slide):
    """找到正文主文本框"""
    candidates = []
    for sh in slide.shapes:
        if not sh.has_text_frame: continue
        text = sh.text_frame.text.strip()
        if len(text) < 15: continue
        left_in = sh.left / 914400
        width_in = sh.width / 914400
        height_in = sh.height / 914400
        # 右侧主文本：left > 4.5in, width > 3in, height > 2in
        if left_in > 4.5 and width_in > 3 and height_in > 2:
            candidates.append(sh)
    if not candidates:
        return None
    # 取最大的
    return max(candidates, key=lambda s: s.width * s.height)


def set_paragraphs(textbox, paragraphs):
    """把文本框内容替换为段落列表，字号自适应"""
    tf = textbox.text_frame

    # 清空现有段落
    for p in list(tf.paragraphs[1:]):
        p._p.getparent().remove(p._p)
    # 第一段清空
    first_p = tf.paragraphs[0]
    for r in list(first_p.runs):
        r._r.getparent().remove(r._r)

    # 计算可容纳内容
    box_w_emu = textbox.width - Emu(91440)  # 减去边距
    box_h_emu = textbox.height - Emu(91440)
    if box_h_emu <= 0: box_h_emu = Emu(914400 * 5)

    # 根据内容量选字号
    total_chars = sum(len(p) for p in paragraphs)
    if total_chars < 100:
        base_size = 16
    elif total_chars < 250:
        base_size = 14
    elif total_chars < 500:
        base_size = 13
    else:
        base_size = 12

    # 逐段填文字，检测溢出则降字号
    size = base_size
    while size >= 9:
        w_in = box_w_emu / 914400
        cpl = max(1, (w_in * 72) / (size * 0.95))
        total_lines = 0
        for p in paragraphs:
            if not p:
                total_lines += 1
                continue
            total_lines += max(1, math.ceil(len(p) / cpl))
        needed_h_pt = total_lines * size * 1.3
        if needed_h_pt * 12700 <= box_h_emu:
            break
        size -= 0.5

    # 填文字
    first_run = first_p.add_run()
    first_run.text = paragraphs[0] if paragraphs else ''
    set_run_font(first_run, size)

    for p_text in paragraphs[1:]:
        p = tf.add_paragraph()
        run = p.add_run()
        run.text = p_text
        set_run_font(run, size)

    # 行距
    for p in tf.paragraphs:
        pPr = p._p.find(qn('a:pPr'))
        if pPr is None:
            pPr = etree.SubElement(p._p, qn('a:pPr'))
        lnSpc = pPr.find(qn('a:lnSpc'))
        if lnSpc is None:
            lnSpc = etree.SubElement(pPr, qn('a:lnSpc'))
        else:
            for c in list(lnSpc): lnSpc.remove(c)
        pct = etree.SubElement(lnSpc, qn('a:spcPct'))
        pct.set('val', '130000')

    return size


def set_run_font(run, size_pt):
    run.font.name = '微软雅黑'
    run.font.size = Pt(size_pt)
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = etree.SubElement(rPr, qn('a:ea'))
    ea.set('typeface', '微软雅黑')


def main():
    applied = 0
    skipped = []
    for snum, slide in enumerate(prs.slides, 1):
        paras = cleaned.get(str(snum), [])
        if not paras:
            continue
        tb = find_body_textbox(slide)
        if tb is None:
            skipped.append(snum)
            continue
        size = set_paragraphs(tb, paras)
        applied += 1
        if snum % 20 == 0:
            print(f"  ...applied {snum}")

    prs.save('output_final.pptx')
    print(f"\n已应用: {applied} 页")
    print(f"跳过(无正文框或空): {skipped}")


if __name__ == "__main__":
    main()
