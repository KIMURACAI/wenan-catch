"""临时检查：解析质量"""
import json
d = json.load(open(r"e:\wenan catch\81work\deck_qimen.json", encoding="utf-8"))
ncase = 0
for s in d["sections"]:
    for c in s["cases"]:
        ncase += 1
        p = c["params"]
        warn = p["warnings"] + c["warnings"]
        shens = [x["shen"] for x in c["cells"] if x["palace"] != 5]
        center = [x["tian"] for x in c["cells"] if x["palace"] == 5]
        ok = "OK  " if not warn else "WARN"
        t = c["title"][:18]
        print(f"{ncase:2d} {t:20s} 格{len(c['cells'])} 中宫={center[0] if center else '':>1s} 八神={len(set(shens))}个 {ok}")
        for w in warn:
            print(f"      ! {w}")
print("案例总数:", ncase)
print()
c1 = d["sections"][9]["cases"][0]
print("案例1 参数:", json.dumps(c1["params"], ensure_ascii=False))
print("案例1 排盘格:")
for x in c1["cells"]:
    print(f'  {x["palace"]}宫 八神={x["shen"]:<3s} 天盘={x["tian"]:<3s} 地盘={x["di"]:<2s} 星={x["star"]:<4s} 门={x["door"]}')
print()
# 重复时旬的两例（表6四川何瑞=案例6? 表15阳宅）找出来
print("== 时旬多行的案例 ==")
for s in d["sections"]:
    for c in s["cases"]:
        if len(c["params"]["shixun"]) > 1:
            print(c["title"], "->", c["params"]["shixun"], "值符last:", c["params"]["zhifu"], "值使:", c["params"]["zhishi"])
