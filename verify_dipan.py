"""最强校验：按遁局规则独立重算地盘（三奇六仪落宫），与源盘地盘干逐格比对。
只读校验，绝不修改源数据。"""
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

SRC = r"C:\Users\Kimura\Documents\xwechat_files\wxid_5ctvyfm60gsr12_0423\msg\file\2026-08\预测案例92-168.docx"

STARS = ["蓬", "芮", "冲", "辅", "禽", "心", "柱", "任", "英"]
DOORS = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
STEMS = "甲乙丙丁戊己庚辛壬癸"
STEM_ORDER = list("戊己庚辛壬癸丁丙乙")  # 三奇六仪固定顺序

# 洛书九宫位次：宫号 → (行, 列)。表格 3x3
# 上排: 巽4 离9 坤2 / 中排: 震3 中5 兑7 / 下排: 艮8 坎1 乾6
PALACE_POS = {4:(0,0), 9:(0,1), 2:(0,2), 3:(1,0), 5:(1,1), 7:(1,2), 8:(2,0), 1:(2,1), 6:(2,2)}


def cell_extract(cell, doc):
    """返回 (spirit, line1_天盘干, line2_地盘干星门)"""
    nested = []
    paras = []
    for child in cell._tc.iterchildren():
        if child.tag.endswith("}tbl"):
            for r in Table(child, doc).rows:
                for c in r.cells:
                    t = c.text.replace("\n", "").replace(" ", "").strip()
                    if t:
                        nested.append(t)
        elif child.tag.endswith("}p"):
            t = Paragraph(child, doc).text.strip()
            if t:
                paras.append(t)
    spirit = "".join(nested)
    line1 = paras[0] if len(paras) > 0 else ""
    line2 = "".join(paras[1:])
    return spirit, line1, line2


def parse_line2(line2):
    """提取地盘干（line2中第一个三奇六仪字符）"""
    for ch in line2:
        if ch in STEMS:
            return ch
    return ""


def compute_dipan(yin_yang, ju):
    """计算地盘：阳遁顺布/阴遁逆布三奇六仪，第ju局从ju宫起戊。
    返回 {宫号: 干}"""
    result = {}
    start = ju
    for i, stem in enumerate(STEM_ORDER):
        if yin_yang == "阳":
            palace = (start - 1 + i) % 9 + 1
        else:
            palace = (start - 1 - i) % 9 + 1
        result[palace] = stem
    return result


doc = Document(SRC)

# 遍历 body 流，收集每个表格前的遁局信息
body = doc.element.body
tables_meta = []
pending = {}
tbl_idx = 0
for child in body.iterchildren():
    if child.tag.endswith("}p"):
        text = Paragraph(child, doc).text.strip()
        CN = {"一":1, "二":2, "三":3, "四":4, "五":5, "六":6, "七":7, "八":8, "九":9}
        m = re.search(r'(阳|阴)遁?[\s]?([一二三四五六七八九1-9])局', text)
        if m:
            raw = m.group(2)
            ju = CN[raw] if raw in CN else int(raw)
            pending = {"yy": m.group(1), "ju": ju, "header": text[:40]}
    elif child.tag.endswith("}tbl"):
        t = Table(child, doc)
        tables_meta.append((pending, t))
        pending = {}

print(f"共 {len(tables_meta)} 表，含遁局信息: {sum(1 for p,_ in tables_meta if p)}\n")

pass_all = True
for ti, (meta, t) in enumerate(tables_meta):
    if not meta:
        print(f"表{ti+1}: ⚠ 未找到遁局信息（无法重算校验）")
        continue

    # 提取源盘地盘干
    source_dipan = {}
    for ri, row in enumerate(t.rows):
        for ci, c in enumerate(row.cells):
            palace = [p for p, (pr, pc) in PALACE_POS.items() if pr == ri and pc == ci]
            if not palace:
                continue
            pnum = palace[0]
            if pnum == 5:
                # 中宫：中心格值即为中宫地盘干
                nested, paras = [], []
                for child in c._tc.iterchildren():
                    if child.tag.endswith("}tbl"):
                        for r in Table(child, doc).rows:
                            for cc in r.cells:
                                t2 = cc.text.replace("\n", "").replace(" ", "").strip()
                                if t2:
                                    nested.append(t2)
                    elif child.tag.endswith("}p"):
                        t2 = Paragraph(child, doc).text.strip()
                        if t2:
                            paras.append(t2)
                source_dipan[pnum] = ("".join(nested) + "".join(paras)).strip()
                continue
            _, _, line2 = cell_extract(c, doc)
            source_dipan[pnum] = parse_line2(line2)

    # 重算期望地盘
    expected = compute_dipan(meta["yy"], meta["ju"])

    # 比对
    mismatches = []
    for pnum in expected:
        exp = expected[pnum]
        src = source_dipan.get(pnum, "?")
        if exp != src:
            mismatches.append(f"宫{pnum}: 应{exp} 源盘{src}")

    if mismatches:
        pass_all = False
        print(f"表{ti+1} ✗ {meta['yy']}遁{meta['ju']}局 地盘不符: {mismatches}")
    else:
        print(f"表{ti+1} ✓ {meta['yy']}遁{meta['ju']}局 地盘全部吻合")

print(f"\n=== 地盘校验: {'全部通过' if pass_all else '存在不符，需人工甄别'} ===")
print("源盘为权威，任何不符仅报告，绝不自动修改")
