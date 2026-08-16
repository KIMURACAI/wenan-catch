"""最终验证：JSON 中的 20 排盘表 + 独立重算地盘比对"""
import json, re

with open(r"e:\wenan catch\qimen_cases.json", "r", encoding="utf-8") as f:
    d = json.load(f)

STARS = ["蓬","芮","冲","辅","禽","心","柱","任","英"]
DOORS = ["休","生","伤","杜","景","死","惊","开"]
SPIRITS = ["值符","螣蛇","太阴","六合","白虎","玄武","九地","九天"]
STEM_ORDER = list("戊己庚辛壬癸丁丙乙")
PALACE_POS = {4:(0,0),9:(0,1),2:(0,2),3:(1,0),5:(1,1),7:(1,2),8:(2,0),1:(2,1),6:(2,2)}
CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}

def compute_dipan(yy, ju):
    out = {}
    for i, stem in enumerate(STEM_ORDER):
        p = (ju - 1 + i) % 9 + 1 if yy == "阳" else (ju - 1 - i) % 9 + 1
        out[p] = stem
    return out

def parse_combined(line2):
    stem, stars, doors = "", [], []
    for ch in line2:
        if ch in "甲乙丙丁戊己庚辛壬癸":
            stem += ch
        elif ch in STARS:
            stars.append(ch)
        elif ch in DOORS:
            doors.append(ch)
    return stem, "".join(stars), "".join(doors)

all_pass = True
total_cases = 0
for si, s in enumerate(d["sections"]):
    for c in s["cases"]:
        total_cases += 1
        grid = c["grid"]
        errs = []
        spirits, doors, stars, dipan = [], [], [], {}
        for ri in range(3):
            for ci in range(3):
                cell = grid[ri][ci]
                pnum = cell["palace"]
                if pnum == 5:
                    dipan[5] = cell.get("center", "")
                    continue
                spirits.append(cell["spirit"])
                st, sts, ds = parse_combined(cell["dipan"])
                dipan[pnum] = st
                stars += list(sts)
                doors += list(ds)
        # 结构检查
        for sname in SPIRITS:
            if spirits.count(sname) != 1:
                errs.append(f"八神[{sname}]出现{spirits.count(sname)}次")
        for dname in DOORS:
            if doors.count(dname) != 1:
                errs.append(f"八门[{dname}]出现{doors.count(dname)}次")
        # 地盘比对
        yy = ju = None
        for h in c["header"]:
            m = re.search(r'(阳|阴)遁?[\s]?([一二三四五六七八九1-9])局', h)
            if m:
                yy = m.group(1)
                r = m.group(2)
                ju = CN[r] if r in CN else int(r)
                break
        if yy:
            exp = compute_dipan(yy, ju)
            for pnum, stem in exp.items():
                src = dipan.get(pnum, "")
                # 源盘地盘干=组合首干，或中心格单值
                if src != stem:
                    errs.append(f"地盘宫{pnum}: 应{stem} 源{src}")
        status = "✓" if not errs else "✗"
        if errs:
            all_pass = False
            print(f"案例{c['index']}: {status} {'; '.join(errs)}")
        else:
            print(f"案例{c['index']}: {status} 通过")

print(f"\n=== 验证: {total_cases} 案例, {'全部通过' if all_pass else '存在问题'} ===")
