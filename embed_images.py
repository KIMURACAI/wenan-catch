"""读取 images/* 图片，缩小到合适尺寸，输出 base64 Data URI 映射 JSON"""
import os
import base64
import json
import cv2
import numpy as np

img_dir = r"e:\wenan catch\images"
output_json = r"e:\wenan catch\base64_map.json"

# 目标：打印质量，A4 内容区约 170mm 宽，200dpi ≈ 1340px
MAX_W = 1200
JPEG_Q = 88

mapping = {}

for i in range(1, 23):
    # 尝试 .png 或 .jpeg
    png = os.path.join(img_dir, f"fig-{i:02d}.png")
    jpg = os.path.join(img_dir, f"fig-{i:02d}.jpeg")
    path = png if os.path.exists(png) else jpg
    if not os.path.exists(path):
        print(f"  fig-{i:02d}: 文件不存在，跳过")
        continue

    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"  fig-{i:02d}: 无法读取，跳过")
        continue

    # 透明通道合成白底
    if len(img.shape) == 3 and img.shape[2] == 4:
        bg = np.full((img.shape[0], img.shape[1], 3), 255, dtype=np.uint8)
        alpha = img[:, :, 3] / 255.0
        for c in range(3):
            bg[:, :, c] = (1 - alpha) * bg[:, :, c] + alpha * img[:, :, c]
        img = bg

    # 转灰度（手稿图是黑白的，保持灰度能减少尺寸）
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    h, w = gray.shape
    if w > MAX_W:
        ratio = MAX_W / w
        new_w = MAX_W
        new_h = int(h * ratio)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 编码为 JPEG base64
    success, buf = cv2.imencode('.jpg', gray, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_Q])
    if not success:
        print(f"  fig-{i:02d}: 编码失败")
        continue

    b64 = base64.b64encode(buf).decode('ascii')
    data_uri = f"data:image/jpeg;base64,{b64}"
    mapping[f"fig-{i:02d}"] = data_uri
    kb = len(b64) * 3 // 4 // 1024
    print(f"  fig-{i:02d}: {gray.shape[1]}x{gray.shape[0]} → {kb}KB")

with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False)

print(f"\n完成！共 {len(mapping)} 张，映射已保存到 {output_json}")
