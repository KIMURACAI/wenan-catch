"""验证排盘表（修正版）：八神嵌套表格段落合并，区分源数据异常与提取bug"""
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"C:\Users\Kimura\Documents\xwechat_files\wxid_5ctvyfm60gsr12_0423\msg\file\2026-08\预测案例92-168.docx"

STARS = ["蓬", "芮", "冲", "辅", "禽", "心", "柱", "任", "英"]
DOORS = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
SPIRITS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
STEMS = "甲乙丙丁戊己庚辛壬癸"


def cell_full(cell, doc):
    """返回 (nested_table_parts, paragraph_parts)"""
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
    return nested, paras


def parse_combined(line2):
    stem = ""
    stars = []
    doors = []
    for ch in line2:
        if ch in STEMS:
            stem += ch
        elif ch in STARS:
            stars.append(ch)
        elif ch in DOORS:
            doors.append(ch)
    return stem, "".join(stars), "".join(doors)


doc = Document(SRC)
print(f"共 {len(doc.tables)} 个排盘表\n")
fail_count = 0

for ti, t in enumerate(doc.tables):
    errors = []
    all_spirits = []
    all_stars = []
    all_doors = []
    center = ""

    for ri, row in enumerate(t.rows):
        for ci, c in enumerate(row.cells):
            nested, paras = cell_full(c, doc)
            if ri == 1 and ci == 1:
                center = "".join(nested + paras).strip()
                continue
            # 八神 = 嵌套表格所有段落合并（螣蛇拆成 螣+蛇）
            spirit = "".join(nested).strip()
            # 剩余段落 = [天盘干, 地盘干+星+门]
            line2 = "".join(paras[1:]) if len(paras) > 1 else ""
            if not spirit:
                errors.append(f"格({ri},{ci}) 无八神")
            if not line2:
                errors.append(f"格({ri},{ci}) 无地盘/星/门")
            all_spirits.append(spirit)
            stem, stars, doors = parse_combined(line2)
            all_stars += list(stars)
            all_doors += list(doors)

    missing_spirits = [s for s in SPIRITS if s not in all_spirits]
    dup_spirits = [s for s in set(all_spirits) if all_spirits.count(s) > 1]
    if missing_spirits:
        errors.append(f"缺八神: {missing_spirits}")
    if dup_spirits:
        errors.append(f"八神重复: {dup_spirits}")

    door_dup = [d for d in set(all_doors) if all_doors.count(d) > 1]
    door_missing = [d for d in DOORS if d not in all_doors]
    if door_dup:
        errors.append(f"八门重复: {door_dup}")
    if door_missing:
        errors.append(f"缺八门: {door_missing}")

    star_dup = [s for s in set(all_stars) if all_stars.count(s) > 1]
    if star_dup:
        errors.append(f"九星重复: {star_dup}")

    if not center:
        errors.append("中心格为空")

    status = "✓" if not errors else "✗"
    if errors:
        fail_count += 1
    print(f"表{ti+1} {status} 八神={len(set(all_spirits))}个 星={len(set(all_stars))}个 门={len(set(all_doors))}个 中宫={center}")
    for e in errors:
        print(f"    - {e}")

print(f"\n=== 汇总: {len(doc.tables)-fail_count}/{len(doc.tables)} 表完全符合规则 ===")
print("注：源数据异常需单独甄别，绝不会自动修改原盘")
