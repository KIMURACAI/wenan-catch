"""
Stage 1 · docx → Deck 结构化模型

解析 预测案例92-168.docx：
- 顺序遍历 body（段落 + 表格），保持相对顺序
- 识别章节头 / 案例头 / 排盘参数块 / 3×3 排盘表
- 排盘单元格 = 嵌套表(八神) + 段落[天盘干, 地盘干+九星+八门]
- 输出 Deck 模型（dataclass），可序列化为 JSON 供后续阶段使用

容错：重复时旬行、错字「天任 星值使」、截断遁局、节气行连写、全半角冒号。
原则：源文字一字不改（只 strip 首尾空白），解析失败只记 warning 不中断。
"""
import json
import re
from dataclasses import dataclass, field, asdict
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

# ---------- 字符集 ----------
STEMS = "甲乙丙丁戊己庚辛壬癸"
STARS = ["蓬", "芮", "冲", "辅", "禽", "心", "柱", "任", "英"]
DOORS = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
SPIRITS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]

# ---------- 参数块正则 ----------
RE_GONGLI = re.compile(r"^公历[:：]")
RE_NONGLI = re.compile(r"^农历[:：]")
RE_SIZHU = re.compile(r"^四柱[:：]")
RE_DUNJU = re.compile(r"^遁局[:：]")
RE_SHIXUN = re.compile(r"^时旬[:：]")
RE_JIEQI = re.compile(r"^[\u4e00-\u9fa5]{1,4}[:：]\d{4}-\d{2}-\d{2}")   # 白露：2011-09-08…
RE_RIKONG = re.compile(r"日空[:：]\s*(\S+)")
RE_ZF = re.compile(r"值符[:：]\s*(天[^\s:：]{1,3})\s*星?\s*值使[:：]\s*([休生伤杜景死惊开])")
RE_XUN = re.compile(r"时旬[:：]\s*([^\s:：]+)")

# ---------- 章节头 ----------
RE_SECTION = re.compile(r"^（[一二三四五六七八九十]+）|^第[一二三四五六七八九十百]+[节章]|^[一二三四五六七八九十]+、")


@dataclass
class CellData:
    palace: int        # 洛书数 1-9
    shen: str = ""     # 八神
    tian: str = ""     # 天盘干
    di: str = ""       # 地盘干
    star: str = ""     # 九星原始字（冲 / 禽芮 / 芮禽），可空(中宫)
    door: str = ""     # 八门原始字，可空(中宫)
    warning: str = ""


@dataclass
class ParamBlock:
    lines: list = field(default_factory=list)        # 参数行原文（顺序）
    gongli: str = ""
    nongli: str = ""
    sizhu: str = ""
    dunju: str = ""          # 含 遁局+日空
    rikong: str = ""
    jieqi: str = ""          # 节气行（可能两对连写）
    shixun: list = field(default_factory=list)       # 时旬行（可能多行）
    shixun_best: str = ""    # 最后一个时旬名（兼容多行）
    zhifu: str = ""          # 值符星（last-wins）
    zhishi: str = ""         # 值使门（last-wins）
    warnings: list = field(default_factory=list)


@dataclass
class Case:
    title: str
    section: str = ""            # 所属节名
    narrative: list = field(default_factory=list)     # 起局缘由（参数块之前的叙述）
    params: ParamBlock = field(default_factory=ParamBlock)
    cells: list = field(default_factory=list)         # list[CellData]，按宫位
    verdict: list = field(default_factory=list)       # 断语 + 判断思路（表之后所有段）
    warnings: list = field(default_factory=list)


@dataclass
class Section:
    title: str
    kind: str = "theory"         # theory | cases
    intro: list = field(default_factory=list)         # 节内、案例前的理论段
    cases: list = field(default_factory=list)


@dataclass
class Deck:
    title: str = "奇门遁甲预测案例"
    author: str = "成慈老师"
    sections: list = field(default_factory=list)      # list[Section]
    warnings: list = field(default_factory=list)


# ---------- 单元格解析 ----------

def cell_full(cell, doc):
    """返回 (nested_table_texts, paragraph_texts)。八神在嵌套表，螣蛇被拆成 螣/蛇 需合并。"""
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
    """地盘干 + 九星 + 八门 无分隔连写 → (di, star, door)。逐字符归表容错空格。"""
    stem, stars, doors = "", [], []
    for ch in line2:
        if ch in STEMS:
            stem += ch
        elif ch in STARS:
            stars.append(ch)
        elif ch in DOORS:
            doors.append(ch)
    return stem, "".join(stars), "".join(doors)


def parse_cells(table, doc):
    """3×3 排盘表 → list[CellData]（按洛书数）。中宫(1,1)只有单干。"""
    luoshu = {
        (0, 0): 4, (0, 1): 9, (0, 2): 2,
        (1, 0): 3, (1, 1): 5, (1, 2): 7,
        (2, 0): 8, (2, 1): 1, (2, 2): 6,
    }
    cells = []
    for ri, row in enumerate(table.rows):
        for ci, c in enumerate(row.cells):
            palace = luoshu[(ri, ci)]
            nested, paras = cell_full(c, doc)
            if palace == 5:
                # 中宫：值符干（可能含嵌套表）
                center = "".join(nested + paras).strip()
                cells.append(CellData(palace=5, tian=center))
                continue
            spirit = "".join(nested).strip()
            tian = paras[0] if len(paras) > 0 else ""
            combined = paras[1] if len(paras) > 1 else ""
            di, star, door = parse_combined(combined)
            w = ""
            if not spirit:
                w = f"格{ri}{ci}无八神"
            if not di and not door:
                w = (w + ";" if w else "") + f"格{ri}{ci}无地盘/星/门"
            cells.append(CellData(palace=palace, shen=spirit, tian=tian,
                                  di=di, star=star, door=door, warning=w))
    return cells


# ---------- 参数块解析 ----------

def parse_params(lines):
    """参数行 → ParamBlock"""
    pb = ParamBlock()
    pb.lines = list(lines)
    for ln in lines:
        s = ln.strip()
        if RE_GONGLI.match(s):
            pb.gongli = s
        elif RE_NONGLI.match(s):
            pb.nongli = s
        elif RE_SIZHU.match(s):
            pb.sizhu = s
        elif RE_DUNJU.match(s):
            pb.dunju = s
            m = RE_RIKONG.search(s)
            if m:
                pb.rikong = m.group(1)
        elif RE_JIEQI.match(s):
            pb.jieqi = s
        elif RE_SHIXUN.match(s):
            pb.shixun.append(s)
            m = RE_XUN.search(s)
            if m and not pb.shixun_best:
                pb.shixun_best = m.group(1)
            mf = RE_ZF.search(s)
            if mf:
                pb.zhifu = mf.group(1)     # last-wins
                pb.zhishi = mf.group(2)    # last-wins
    # 时旬多行但值符相同 → 不算怪癖；多行不同 → 提示
    if len(pb.shixun) > 1:
        pb.warnings.append(f"时旬多行({len(pb.shixun)}): {pb.shixun}")
    return pb


def _is_section_header(text):
    return bool(RE_SECTION.match(text)) and len(text) <= 30


def _is_case_header(text):
    return text.startswith("案例")


def _is_param_line(s):
    return (RE_GONGLI.match(s) or RE_NONGLI.match(s) or RE_SIZHU.match(s)
            or RE_DUNJU.match(s) or RE_SHIXUN.match(s) or RE_JIEQI.match(s))


def _extract_param_block(narrative):
    """从叙述段尾部切出参数块（允许中间空段），返回 (param_lines, remaining_narrative)"""
    params = []
    i = len(narrative) - 1
    # 从尾部收集参数行，遇到非空非参数行即停
    while i >= 0:
        t = narrative[i]
        if not t.strip():
            i -= 1
            continue
        if _is_param_line(t.strip()):
            params.append(t)
            i -= 1
        else:
            break
    params.reverse()
    remaining = narrative[: i + 1]
    return params, remaining


def parse_docx(path):
    doc = Document(path)
    deck = Deck()

    cur_section = None
    cur_case = None

    def flush_case():
        nonlocal cur_case
        if cur_case is not None:
            if cur_section is not None:
                cur_section.cases.append(cur_case)
            cur_case = None

    def flush_section():
        nonlocal cur_section
        if cur_section is not None:
            if cur_section.cases:
                cur_section.kind = "cases"
            deck.sections.append(cur_section)
        cur_section = None

    body = doc.element.body
    for el in body.iterchildren():
        tag = el.tag.split("}")[-1]
        if tag == "p":
            t = Paragraph(el, doc).text.strip()
            if not t:
                continue
            if cur_section is None:
                # 第一个有效段：简介区（标题=第一个非空段）
                cur_section = Section(title=t)
                continue
            if _is_case_header(t):
                flush_case()
                cur_case = Case(title=t, section=cur_section.title)
                pending_paras = []
                continue
            if _is_section_header(t):
                flush_case()
                flush_section()
                cur_section = Section(title=t)
                pending_paras = []
                continue
            # 普通段：归属当前 case 的 narrative/verdict，或 section.intro
            if cur_case is not None:
                if cur_case.cells:
                    cur_case.verdict.append(t)
                else:
                    cur_case.narrative.append(t)
            else:
                cur_section.intro.append(t)
        elif tag == "tbl":
            # 表 = 当前案例的排盘表
            if cur_case is None:
                # 没有 case 上下文，用当前 section 兜底
                cur_case = Case(title=cur_section.title if cur_section else "未命名案例",
                                section=cur_section.title if cur_section else "")
            # 从 narrative 尾部切参数块
            params, narr = _extract_param_block(cur_case.narrative)
            cur_case.narrative = narr
            cur_case.params = parse_params(params)
            cur_case.cells = parse_cells(Table(el, doc), doc)
            for c in cur_case.cells:
                if c.warning:
                    cur_case.warnings.append(f"[{c.palace}宫] {c.warning}")
            pending_paras = []

    flush_case()
    flush_section()

    # 若没有解析出任何案例，报告
    n_cases = sum(len(s.cases) for s in deck.sections)
    if n_cases == 0:
        deck.warnings.append("未解析到任何案例")
    return deck


def deck_to_dict(deck):
    return asdict(deck)


def dump(path, out_json):
    deck = parse_docx(path)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(deck_to_dict(deck), f, ensure_ascii=False, indent=2)
    ns = len(deck.sections)
    nc = sum(len(s.cases) for s in deck.sections)
    print(f"章节 {ns}，案例 {nc}")
    for s in deck.sections:
        print(f"  [{s.kind}] {s.title}  (案例 {len(s.cases)}, 理论段 {len(s.intro)})")
    if deck.warnings:
        print("Deck warnings:", deck.warnings)
    return deck


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else r"e:\wenan catch\预测案例92-168.docx"
    out = sys.argv[2] if len(sys.argv) > 2 else r"e:\wenan catch\81work\deck_qimen.json"
    dump(src, out)
