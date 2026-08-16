"""用 Playwright 生成带图片的 PDF"""
import asyncio
from playwright.sync_api import sync_playwright
import os

html_path = r"e:\wenan catch\风水下罗经秘法.html"
pdf_path = r"e:\wenan catch\风水下罗经秘法.pdf"

# 获取文件的 file:// URL
abs_path = os.path.abspath(html_path)
file_url = "file:///" + abs_path.replace("\\", "/")

print(f"HTML: {file_url}")
print("启动 Playwright 渲染...(含 22 张图，可能需要一些时间)")

with sync_playwright() as p:
    # 用 Chromium (Playwright 自带)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 加载页面并等待网络空闲 + 额外 3 秒让图片渲染
    page.goto(file_url, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # 截图检查图片是否加载
    page.screenshot(path=r"e:\wenan catch\screenshot_check.png", full_page=True)

    # 生成 PDF
    page.pdf(
        path=pdf_path,
        format="A4",
        margin={"top": "14mm", "bottom": "18mm", "left": "18mm", "right": "18mm"},
        print_background=True,
    )

    browser.close()

pdf_size = os.path.getsize(pdf_path)
print(f"PDF 生成完成！大小: {pdf_size/1024:.0f}KB")

# 数页数
import re
with open(pdf_path, 'rb') as f:
    data = f.read()
pages = len(re.findall(b'/Type\s*/Page[^s]', data))
print(f"PDF 页数: {pages}")
