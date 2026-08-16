"""分析八门旋转规律：用已验证正确的19表确定值使随时宫的布门规则，
用于推断表16缺失/重复的门应为何门。只读，不改数据。"""
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
import re

SRC = r"C:\Users\Kimura\Documents\xwechat_files\wxid_5ctvyfm60gsr12_0423\msg\file\2026-08\预测案例92-168.docx"

STARS = ["蓬","芮","冲","辅","禽","心","柱","任","英"]
DOORS = ["休","生","伤","杜","景","死","惊","开"]
STEMS = "甲乙丙丁戊己庚辛壬癸"

# 洛书九宫位置: 宫号 -> (行,列)
PALACE_POS = {4:(0,0), 9:(0,1), 2:(0,2), 3:(1,0), 5:(1,1), 7:(1,2), 8:(2,0), 1:(2,1), 6:(2,2)}
POS_PALACE = {v:k for k,v in PALACE_POS.items()}
# 八卦方位(后天): 宫号 -> 方位，用于判断顺逆
PALACE_COMPASS = {1:"北",2:"西南",3:"东",4:"东南",5:"中",6:"西北",7:"西",8:"东北",9:"南"}
# 顺时针顺序: 震3东 -> 巽4东南 -> 离9南 -> 坤2西南 -> 兑7西 -> 乾6西北 -> 坎1北 -> 艮8东北
CLOCKWISE = [3,4,9,2,7,6,1,8]


def cell_parts(cell, doc):
    nested, paras = [], []
    for ch in cell._tc.iterchildren():
        if ch.tag.endswith("}tbl"):
            for r in Table(ch, doc).rows:
                for c in r.cells:
                    t = c.text.replace("\n","").replace(" ","").strip()
                    if t: nested.append(t)
        elif ch.tag.endswith("}p"):
            t = Paragraph(ch, doc).text.strip()
            if t: paras.append(t)
    return "".join(nested), paras


def door_of(line2):
    for ch in line2:
        if ch in DOORS:
            return ch
    return None


doc = Document(SRC)
# 收集每表 值使 + door->palace
tables_data = []
pending = {}
for child in doc.element.body.iterchildren():
    if child.tag.endswith("}p"):
        text = Paragraph(child, doc).text.strip()
        m = re.search(r'值使：([\u4e00-\u9fff]+)', text)
        if m:
            pending["shishi"] = m.group(1)[0] if m.group(1).endswith("门") else m.group(1)
        m2 = re.search(r'(阳|阴)遁?[\s]?([一二三四五六七八九1-9])局', text)
        if m2:
            CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
            r = m2.group(2)
            pending["ju"] = CN[r] if r in CN else int(r)
            pending["yy"] = m2.group(1)
    elif child.tag.endswith("}tbl"):
        t = Table(child, doc)
        door_palace = {}
        for ri, row in enumerate(t.rows):
            for ci, c in enumerate(row.cells):
                pnum = POS_PALACE.get((ri,ci))
                if pnum is None or pnum == 5:
                    continue
                _, paras = cell_parts(c, doc)
                line2 = "".join(paras[1:])
                d = door_of(line2)
                if d:
                    door_palace[pnum] = d
        tables_data.append({"meta": pending, "door_palace": door_palace})
        pending = {}

# 对每个表，找值使门落宫，然后分析布门顺序
print("=== 八门旋转规律分析（按顺时针宫序排列每宫之门）===\n")
for ti, td in enumerate(tables_data):
    dp = td["door_palace"]
    if len(dp) != 8:
        continue
    meta = td["meta"]
    shishi = meta.get("shishi", "?")
    # 值使门在哪宫
    shishi_palace = [p for p,d in dp.items() if d == shishi]
    if not shishi_palace:
        continue
    sp = shishi_palace[0]
    # 从值使宫起顺时针排列门
    seq = []
    idx = CLOCKWISE.index(sp)
    for k in range(8):
        p = CLOCKWISE[(idx+k)%8]
        seq.append(f"{p}:{dp.get(p,'?')}")
    print(f"表{ti+1} 值使[{shishi}]@{sp}宫 顺时针: {' '.join(seq)}")
