"""还原 HTML 中的图片路径为相对路径"""
import re

html_path = r'e:\wenan catch\风水下罗经秘法.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# file:///E:/wenan%20catch/images/fig-XX.ext → images/fig-XX.ext
html = re.sub(r'src="file:///E:/wenan%20catch/images/(fig-\d+\.[^"]+)"', r'src="images/\1"', html)

count = html.count('src="images/')
print(f'还原了，共 {count} 处 src')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'HTML 大小: {len(html.encode("utf-8"))/1024:.0f}KB')
