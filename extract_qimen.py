"""从 预测案例92-168.docx 完整提取有序文档结构：简介 → 理论 → 分类节(含引言+案例)
排盘逐格提取（八神来自嵌套表格），表16 应用规则验证修正（乾6宫 休→生）。
润色只做格式（合并断行、规范化标点），不改文字内容。"""
import json, re
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = r"C:\Users\Kimura\Documents\xwechat_files\wxid_5ctvyfm60gsr12_0423\msg\file\2026-08\预测案例92-168.docx"
OUT = r"e:\wenan catch\qimen_cases.json"

POS_PALACE = {(0,0):4, (0,1):9, (0,2):2, (1,0):3, (1,1):5, (1,2):7, (2,0):8, (2,1):1, (2,2):6}
SECTION_RE = re.compile(r'^((?:第[一二三四五六七八九十]+节|十[二三]?、)[^：]{2,20})$')
CASE_RE = re.compile(r'^案例[一二三四五六七八九十]*：')
SENT_END = "。！？；：…"


def cell_parts(cell, doc):
    nested, paras = [], []
    for ch in cell._tc.iterchildren():
        if ch.tag.endswith("}tbl"):
            for r in Table(ch, doc).rows:
                for c in r.cells:
                    t = c.text.replace("\n", "").replace(" ", "").strip()
                    if t:
                        nested.append(t)
        elif ch.tag.endswith("}p"):
            t = Paragraph(ch, doc).text.strip()
            if t:
                paras.append(t)
    return "".join(nested), paras


def parse_table(t, doc):
    grid, center = [], ""
    for ri in range(3):
        row = []
        for ci in range(3):
            pnum = POS_PALACE[(ri, ci)]
            cell = t.rows[ri].cells[ci]
            spirit, paras = cell_parts(cell, doc)
            if pnum == 5:
                center = (spirit + "".join(paras)).strip()
                row.append({"palace": 5, "center": center})
                continue
            row.append({
                "palace": pnum,
                "spirit": spirit,
                "tiangan": paras[0] if paras else "",
                "dipan": "".join(paras[1:]).strip(),
            })
        grid.append(row)
    return grid, center


def normalize(text):
    t = re.sub(r'(?<=[\u4e00-\u9fff]),', '，', text)
    t = re.sub(r'(?<=[\u4e00-\u9fff]);', '；', t)
    t = re.sub(r'(?<=[\u4e00-\u9fff]):', '：', t)
    t = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', t)
    return t.strip()


def merge_paras(paras):
    merged, buf = [], ""
    for p in paras:
        p = normalize(p)
        if not p:
            continue
        if not buf:
            buf = p
        elif buf[-1] in SENT_END or p[0] in "①②③④⑤⑥⑦⑧⑨⑩（(0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" or re.match(r'^[（(]?[一二三四五六七八九十]+[、.]', p):
            merged.append(buf)
            buf = p
        else:
            buf += p
    if buf:
        merged.append(buf)
    return merged


doc = Document(SRC)
items = []
for child in doc.element.body.iterchildren():
    if child.tag.endswith("}p"):
        items.append(("p", Paragraph(child, doc).text))
    elif child.tag.endswith("}tbl"):
        items.append(("tbl", Table(child, doc)))

# 预扫描：每个表格的 标题/起局header/分析范围
tbl_info = {}  # idx -> {"title": str, "header": [], "end": int}
for idx, (kind, val) in enumerate(items):
    if kind != "tbl":
        continue
    # 标题 + 起局header：往回找 case 标题，其后的段为起局信息
    title = ""
    header = []
    title_idx = None
    for j in range(idx - 1, max(-1, idx - 15), -1):
        k, v = items[j]
        if k == "p":
            if CASE_RE.match(v.strip()):
                title = v.strip()
                title_idx = j
                break
            header.append(v.strip())
    header.reverse()
    # 分析范围
    end = idx
    for j in range(idx + 1, len(items)):
        k, v = items[j]
        if k == "tbl":
            end = j - 1
            break
        v = v.strip()
        if not v:
            end = j
            continue
        if CASE_RE.match(v) or SECTION_RE.match(v):
            end = j - 1
            break
        end = j
    tbl_info[idx] = {"title": title, "header": header, "end": end}

# 分析范围占用集合（避免重复抓取）
analysis_claimed = set()
for idx, info in tbl_info.items():
    for j in range(idx + 1, info["end"] + 1):
        analysis_claimed.add(j)

# ===== 主遍历 =====
preface_bio = []
theory = []
sections = []
current_section = None
current_intro = []
in_bio = False
bio_done = False
case_counter = 0

for idx, (kind, val) in enumerate(items):
    # 分析占用段直接跳过
    if idx in analysis_claimed:
        continue

    if kind == "tbl":
        if current_section is None:
            continue
        info = tbl_info[idx]
        grid, center = parse_table(val, doc)
        case_counter += 1
        if case_counter == 16:
            c = grid[2][2]
            if "休" in c["dipan"]:
                c["dipan"] = c["dipan"].replace("休", "生", 1)
                c["fixed"] = "乾6宫门休→生（据八门旋转规则校正）"
        current_section["cases"].append({
            "index": case_counter,
            "title": info["title"],
            "header": merge_paras(info["header"]),
            "grid": grid,
            "center": center,
        })
        continue

    text = val.strip()
    if not text:
        continue

    # 简介区
    if "成慈老师个人简介" in text or ("茅山派第" in text and not bio_done):
        in_bio = True
    if in_bio and not bio_done:
        if SECTION_RE.match(text) or "在门、星、神三者中" in text:
            in_bio = False
            bio_done = True
        else:
            preface_bio.append(text)
            continue

    # 分类节
    if SECTION_RE.match(text):
        if current_section is not None:
            current_section["intro"] = merge_paras(current_intro)
        current_section = {"title": text, "intro": [], "cases": []}
        sections.append(current_section)
        current_intro = []
        continue

    if current_section is None:
        theory.append(text)
    else:
        current_intro.append(text)

if current_section is not None:
    current_section["intro"] = merge_paras(current_intro)

preface_bio = merge_paras(preface_bio)
theory = merge_paras(theory)

# 把案例的 analysis 填回（用 tbl_info 的 end 区间文本）
for idx, info in tbl_info.items():
    if idx not in [items.index((k, v)) for k, v in items if k == "tbl"]:
        pass
# 直接重新抓分析文本：从表格后到 end 的段落
case_list = []
for s in sections:
    for c in s["cases"]:
        case_list.append((c, None))

# 从 items 中定位每个案例的分析文本
case_ptr = [c for s in sections for c in s["cases"]]
ci = 0
for idx, info in tbl_info.items():
    if ci >= len(case_ptr):
        break
    c = case_ptr[ci]
    analysis = []
    for j in range(idx + 1, info["end"] + 1):
        k, v = items[j]
        if k == "p":
            t = v.strip()
            if t:
                analysis.append(t)
    c["analysis"] = merge_paras(analysis)
    ci += 1

data = {
    "source": SRC,
    "preface": {"bio": preface_bio, "theory": theory},
    "sections": sections,
    "total_cases": case_counter,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 校验字数（无重复）
total = sum(len(p) for p in preface_bio) + sum(len(p) for p in theory)
all_blocks = []
all_blocks += preface_bio + theory
for s in sections:
    all_blocks += s["intro"]
    for c in s["cases"]:
        all_blocks += c["analysis"]
        total += sum(len(p) for p in c["analysis"])
    total += sum(len(p) for p in s["intro"])
from collections import Counter
cnt = Counter(b for b in all_blocks if len(b) > 30)
dups = sum(1 for k, v in cnt.items() if v > 1)
print(f"提取完成: 简介{len(preface_bio)}段 理论{len(theory)}段 {len(sections)}节 {case_counter}案例")
print(f"总字符: {total}  重复长段落: {dups}")
