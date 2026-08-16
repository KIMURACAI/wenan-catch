"""Playwright 生成含图 PDF"""
from playwright.sync_api import sync_playwright
import os, re

html = os.path.abspath(r"e:\wenan catch\风水下罗经秘法.html")
url = "file:///" + html.replace("\\", "/")
pdf = r"e:\wenan catch\风水下罗经秘法.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(3000)  # 等图片加载
    page.pdf(path=pdf, format="A4", margin={"top": "14mm", "right": "18mm", "bottom": "18mm", "left": "18mm"}, print_background=True)
    browser.close()

size = os.path.getsize(pdf)
with open(pdf, "rb") as f:
    pages = len(re.findall(b"/Type\s*/Page[^s]", f.read()))
print(f"PDF: {size/1024:.0f}KB, {pages} 页")
