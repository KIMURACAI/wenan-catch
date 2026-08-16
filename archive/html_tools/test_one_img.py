"""生成测试 HTML：只用 1 张图 + 全部文字，看 Edge 能否渲出图"""
import os, base64, cv2, numpy as np

html_path = r'e:\wenan catch\test_one_img.html'
orig_html = r'e:\wenan catch\风水下罗经秘法.html'
img_path = r'e:\wenan catch\images\fig-01.png'

# 读图缩小到 1200px
img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
h, w = img.shape
if w > 1200:
    ratio = 1200 / w
    img = cv2.resize(img, (1200, int(h * ratio)), interpolation=cv2.INTER_AREA)
success, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
b64 = base64.b64encode(buf).decode('ascii')
data_uri = f'data:image/jpeg;base64,{b64}'
print(f'图尺寸: {img.shape[1]}x{img.shape[0]}, base64: {len(b64)//1024}KB')

# 读原 HTML
with open(orig_html, 'r', encoding='utf-8') as f:
    html = f.read()

# 找到所有 figure 替换为只有 fig-01 用 base64，其他 figure 隐掉
count = 0
def replace_fig(m):
    global count
    count += 1
    if count == 1:
        # 第一张图用 base64
        return m.group(0).replace('src="images/fig-01.png"', f'src="{data_uri}"')
    else:
        # 其他图位：隐掉 img，只留文字
        lines = m.group(0).split('\n')
        filtered = []
        for line in lines:
            if '<img ' in line:
                continue
            filtered.append(line)
        return '\n'.join(filtered)

import re
html = re.sub(r'<figure class="fig">.*?</figure>', replace_fig, html, flags=re.DOTALL)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'测试 HTML 已生成: {html_path}')
print(f'HTML 大小: {len(html.encode("utf-8"))//1024}KB')
