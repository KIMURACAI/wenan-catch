"""
Stage 2 · 标准奇门排盘图（python-pptx 原生 shape，矢量）

依据标准奇门遁甲盘版式（洛书九宫，上南下北）：
  戴九履一、左三右七、二四为肩、六八为足，中五寄坤。
每宫自上而下竖排五层：八神 → 天盘干 → 九星 → 八门 → 地盘干。
- 值符宫（八神==值符）：浅蓝底 + 2pt 粗边框，视觉焦点
- 值使宫（门==值使门）：门字染暗红 + 下方红点，标注值使
- 中五宫：暖沙底色，只放中宫干 + 标注
配色沿用 Kami token：羊皮纸 #f5f4ed / 中宫 #e8e6dc / 墨蓝 #1B365D
/ 淡墨蓝 #2D5A8A / 石灰 #6b6a64 / 八神暗红 #8B0000 / 天盘干近黑 #141413
"""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from lxml import etree
from pptx.oxml.ns import qn

# ---------- 洛书宫位（row, col）与卦名 ----------
# 戴九履一：9 在上中，1 在下中；左三右七；二四为肩；六八为足
LUOSHU = {4: (0, 0), 9: (0, 1), 2: (0, 2),
          3: (1, 0), 5: (1, 1), 7: (1, 2),
          8: (2, 0), 1: (2, 1), 6: (2, 2)}
PALACE_NAMES = {4: "巽四", 9: "离九", 2: "坤二",
                3: "震三", 5: "中五", 7: "兑七",
                8: "艮八", 1: "坎一", 6: "乾六"}
DIRECTIONS = {4: "东南", 9: "南", 2: "西南",
              3: "东", 5: "中", 7: "西",
              8: "东北", 1: "北", 6: "西北"}

# ---------- Kami token ----------
PARCH = RGBColor(0xF5, 0xF4, 0xED)
SAND = RGBColor(0xE8, 0xE6, 0xDC)
ZF_TINT = RGBColor(0xE4, 0xEC, 0xF5)    # 值符宫浅蓝底
INK = RGBColor(0x1B, 0x36, 0x5D)
INK_LIGHT = RGBColor(0x2D, 0x5A, 0x8A)
STONE = RGBColor(0x6B, 0x6A, 0x64)
SPIRIT_RED = RGBColor(0x8B, 0x00, 0x00)
NEAR_BLACK = RGBColor(0x14, 0x14, 0x13)


def _set_font_run(run, size, color, bold=False, font='微软雅黑'):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = etree.SubElement(rPr, qn('a:ea'))
    ea.set('typeface', font)


def _add_text(slide, left_in, top_in, w_in, h_in, text, size_pt,
              color, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(left_in), Inches(top_in),
                                  Inches(w_in), Inches(h_in))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    _set_font_run(r, size_pt, color, bold)
    return tb


def draw_qimen_chart(slide, cells, left_in, top_in, size_in, zhishi_door=None):
    """cells: list[CellData]。画标准竖排五层九宫排盘图。
    zhishi_door: 值使门（单字，如 '死'），所在宫的门会标红+红点。"""
    cs = size_in / 3.0
    zf_palace = None
    for c in cells:
        if c.shen == "值符":
            zf_palace = c.palace
            break

    for c in cells:
        palace = c.palace
        row, col = LUOSHU[palace]
        x = left_in + col * cs
        y = top_in + row * cs
        cx = x + cs / 2.0

        is_center = (palace == 5)
        is_zf = (not is_center and palace == zf_palace)
        fill = SAND if is_center else (ZF_TINT if is_zf else PARCH)
        border_w = 2.0 if is_zf else 0.75

        # 宫格矩形
        rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      Inches(x), Inches(y), Inches(cs), Inches(cs))
        rect.fill.solid()
        rect.fill.fore_color.rgb = fill
        rect.line.color.rgb = INK
        rect.line.width = Pt(border_w)
        rect.shadow.inherit = False

        if is_center:
            # 中五宫：中宫干大字 + 标注
            t = c.tian or ""
            if len(t) > 1:
                t = t[-1]
            _add_text(slide, x, y + cs * 0.18, cs, cs * 0.5, t, 18, INK,
                      bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            _add_text(slide, x, y + cs - 0.28, cs, 0.2, "中五宫", 8, STONE,
                      align=PP_ALIGN.CENTER)
            continue

        # ---- 竖排五层 ----
        # 1) 宫名 + 方位（顶）
        _add_text(slide, cx - cs * 0.5, y + 0.02, cs, 0.2,
                  f"{PALACE_NAMES[palace]} · {DIRECTIONS[palace]}",
                  8.5, INK, bold=True, align=PP_ALIGN.CENTER)
        # 2) 八神
        _add_text(slide, cx - cs * 0.4, y + 0.20, cs * 0.8, 0.2,
                  c.shen, 9, SPIRIT_RED, align=PP_ALIGN.CENTER)
        # 3) 天盘干（正中大字）
        _add_text(slide, cx - cs * 0.42, y + cs * 0.28, cs * 0.84, cs * 0.26,
                  c.tian, 16, NEAR_BLACK, bold=True,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        # 4) 九星
        star_txt = ("天" + c.star + "星") if c.star else ""
        _add_text(slide, cx - cs * 0.4, y + cs * 0.52, cs * 0.8, 0.2,
                  star_txt, 9, INK, align=PP_ALIGN.CENTER)
        # 5) 八门（值使宫标红 + 红点）
        door_txt = (c.door + "门") if c.door else ""
        is_zs = (c.door == zhishi_door and c.door)
        door_color = SPIRIT_RED if is_zs else INK_LIGHT
        _add_text(slide, cx - cs * 0.4, y + cs * 0.70, cs * 0.8, 0.2,
                  door_txt, 9, door_color, align=PP_ALIGN.CENTER)
        # 6) 地盘干
        _add_text(slide, cx - cs * 0.4, y + cs * 0.88, cs * 0.8, 0.22,
                  c.di, 9.5, STONE, align=PP_ALIGN.CENTER)
        # 值使红点
        if is_zs:
            _add_text(slide, cx + 0.18, y + cs * 0.70, 0.2, 0.2,
                      "●", 6, SPIRIT_RED, align=PP_ALIGN.CENTER)


def add_chart_caption(slide, text, left_in, top_in, w_in=8.0):
    _add_text(slide, (13.333 - w_in) / 2, top_in, w_in, 0.25,
              text, 10, STONE, align=PP_ALIGN.CENTER)
