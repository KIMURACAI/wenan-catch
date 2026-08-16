"""把 HTML 中的图片路径改为绝对 file:/// 路径"""
import os

html_path = r'e:\wenan catch\风水下罗经秘法.html'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# images/fig-XX.png → file:///E:/wenan%20catch/images/fig-XX.png
# images/fig-XX.jpeg → file:///E:/wenan%20catch/images/fig-XX.jpeg
import re

def repl(m):
    path = m.group(1)
    # URL 编码空格
    url_path = path.replace(' ', '%20')
    return f'src="file:///E:/wenan%20catch/{url_path}"'

new_html = re.sub(r'src="(images/fig-\d+\.[^"]+)"', repl, html)
count = new_html.count('src="file:///')
print(f'替换了 {count} 处 src 为绝对路径')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(new_html)
print('OK')
