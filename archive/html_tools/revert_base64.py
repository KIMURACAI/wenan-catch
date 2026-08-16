"""把 base64 data URI 还原为文件路径"""
import re, json

html_path = r'e:\wenan catch\风水下罗经秘法.html'
map_path = r'e:\wenan catch\base64_map.json'

with open(map_path, 'r', encoding='utf-8') as f:
    mapping = json.load(f)

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

for name, data_uri in mapping.items():
    png_path = f'images/{name}.png'
    jpg_path = f'images/{name}.jpeg'
    count = html.count(data_uri)
    if count == 0:
        print(f'  {name}: 未找到 data URI，跳过')
        continue
    # 试 png 路径
    html = html.replace(data_uri, png_path, 1)
    print(f'  {name}: data URI → {png_path} ({count}处)')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML 大小: {len(html.encode("utf-8"))/1024:.0f}KB')
