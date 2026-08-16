"""验证 HTML 中排盘表与 JSON 数据一致"""
import json, re

with open(r"e:\wenan catch\qimen_cases.json", "r", encoding="utf-8") as f:
    d = json.load(f)
with open(r"e:\wenan catch\奇门遁甲预测案例-课程.html", "r", encoding="utf-8") as f:
    html = f.read()

# 提取 HTML 中所有排盘表
tables = re.findall(r'<table class="qimen">(.*?)</table>', html, re.DOTALL)
print(f"HTML 排盘表数量: {len(tables)}")

# 校验每个表的关键内容是否出现
fail = 0
case_n = 0
for s in d["sections"]:
    for c in s["cases"]:
        case_n += 1
        t = tables[case_n - 1]
        # 检查该案例所有单元格字符串
        ok = True
        for row in c["grid"]:
            for cell in row:
                if cell["palace"] == 5:
                    continue
                for val in [cell["spirit"], cell["tiangan"], cell["dipan"]]:
                    if val and val not in t:
                        ok = False
                        print(f"  案例{case_n} 缺: {val}")
        if c["index"] == 16:
            # 表16 应含修正后的 乙蓬生，不含 乙蓬休
            if "乙蓬生" not in t:
                print("  表16 缺 乙蓬生")
                ok = False
            if "乙蓬休" in t:
                print("  表16 仍含 乙蓬休 (未修正)")
                ok = False
        if not ok:
            fail += 1

print(f"\n=== HTML 排盘校验: {len(tables)-fail}/{len(tables)} 表一致 ===")
