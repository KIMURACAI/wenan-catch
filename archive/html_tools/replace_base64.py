"""把 HTML 中的图片 src 替换为 base64 data URI"""
import json
import re

html_path = r"e:\wenan catch\风水下罗经秘法.html"
map_path = r"e:\wenan catch\base64_map.json"

with open(map_path, 'r', encoding='utf-8') as f:
    mapping = json.load(f)

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 替换所有 src="images/fig-XX.*" 为 data URI
def replace_src(match):
    orig = match.group(0)
    # 提取文件名: images/fig-01.png
    path = match.group(1)
    # 去掉 images/ 前缀和扩展名
    base = path.split('/')[-1]  # fig-01.png
    name = base.rsplit('.', 1)[0]  # fig-01
    if name in mapping:
        return f'src="{mapping[name]}"'
    print(f"  ⚠️ 未找到 {name} 的映射")
    return orig

new_html, count = re.subn(r'src="(images/fig-\d+\.[^"]+)"', replace_src, html)
print(f"替换了 {count} 处 src")

# 估算文件大小增幅
import os
old_size = len(html.encode('utf-8'))
new_size = len(new_html.encode('utf-8'))
print(f"HTML 大小: {old_size/1024:.0f}KB → {new_size/1024:.0f}KB")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_html)

print("✅ 完成")
