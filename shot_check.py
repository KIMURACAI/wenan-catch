"""截图检查：案例1排盘页 + 表16页"""
import re
from playwright.sync_api import sync_playwright

src = r"e:\wenan catch\奇门遁甲预测案例-课程.html"
with open(src, "r", encoding="utf-8") as f:
    html = f.read()
tmp = src.replace(".html", "_p.html")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(html)

url = "file:///" + tmp.replace("\\", "/")
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 790})
    pg.goto(url, wait_until="domcontentloaded", timeout=20000)
    pg.wait_for_timeout(2000)
    # 案例1 = 排盘页。找包含"为何东来"且含 table.qimen 的 section
    sections = pg.query_selector_all("section.slide")
    print(f"总sections: {len(sections)}")
    # 案例1排盘页：搜索标题
    for i, sec in enumerate(sections):
        txt = sec.inner_text()
        if "为何东来" in txt and "六合" in txt and "值符" in txt:
            sec.screenshot(path=r"e:\wenan catch\shot_case1.png")
            print(f"截图 案例1 排盘页 (slide {i+1})")
            break
    # 表16页
    for i, sec in enumerate(sections):
        txt = sec.inner_text()
        if "河南一朋友" in txt and "乙蓬生" in txt:
            sec.screenshot(path=r"e:\wenan catch\shot_case16.png")
            print(f"截图 表16 排盘页 (slide {i+1})")
            break
    b.close()

import os
for f in ["shot_case1.png", "shot_case16.png"]:
    path = rf"e:\wenan catch\{f}"
    if os.path.exists(path):
        print(f"{f}: {os.path.getsize(path)/1024:.0f}KB")
