"""用 1.png 作为参考风格，AI 匹配处理其他所有图片"""
import os
import cv2
import numpy as np

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
folder = os.path.join(desktop, "配图")

def read_image(path):
    """读取图片，统一转成 8bit 灰度"""
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None
    # 透明通道合成白底
    if len(img.shape) == 3 and img.shape[2] == 4:
        bg = np.full((img.shape[0], img.shape[1], 3), 255, dtype=np.uint8)
        alpha = img[:, :, 3] / 255.0
        for c in range(3):
            bg[:, :, c] = (1 - alpha) * bg[:, :, c] + alpha * img[:, :, c]
        img = bg
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

def save_image(path, img):
    ext = os.path.splitext(path)[1].lower()
    quality = 95 if ext in ('.jpg', '.jpeg') else None
    if quality:
        cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])[1].tofile(path)
    else:
        cv2.imencode('.png', img)[1].tofile(path)

def analyze_style(img):
    """分析参考图的视觉特征"""
    hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
    cdf = hist.cumsum()
    cdf = cdf / cdf[-1]
    lo = np.searchsorted(cdf, 0.02)  # 2% 阴影点
    hi = np.searchsorted(cdf, 0.98)  # 98% 高光点
    mean = np.mean(img)
    std = np.std(img)
    return {'lo': lo, 'hi': hi, 'mean': mean, 'std': std, 'hist': hist}

def match_style(img, ref_stats):
    """把输入图的风格匹配到参考图"""
    # 1. 轻度去噪
    denoised = cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)

    # 2. 自适应直方图均衡（CLAHE）— 让细节清晰
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 3. 直方图匹配到参考图
    ref_hist = ref_stats['hist']
    target = np.zeros(256, dtype=np.uint8)
    src_hist = cv2.calcHist([enhanced], [0], None, [256], [0, 256]).flatten()
    src_cdf = src_hist.cumsum() / src_hist.sum()
    ref_cdf = ref_hist.cumsum() / ref_hist.sum()

    # 构建映射表
    map_table = np.zeros(256, dtype=np.uint8)
    j = 0
    for i in range(256):
        while j < 255 and ref_cdf[j] < src_cdf[i]:
            j += 1
        map_table[i] = j

    matched = cv2.LUT(enhanced, map_table)

    # 4. 轻度锐化
    sharpen = np.array([[-0.3, -0.3, -0.3],
                        [-0.3,  3.4, -0.3],
                        [-0.3, -0.3, -0.3]], dtype=np.float32)
    result = cv2.filter2D(matched, -1, sharpen)

    return result

# 第一步：分析参考图 1.png
ref_path = os.path.join(folder, "1.png")
ref_img = read_image(ref_path)
if ref_img is None:
    print("⚠️ 无法读取 1.png")
    exit()

ref_stats = analyze_style(ref_img)
print(f"参考图 1.png: lo={ref_stats['lo']}, hi={ref_stats['hi']}, mean={ref_stats['mean']:.0f}, std={ref_stats['std']:.0f}")

# 第二步：处理所有其他图片
extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
files = sorted([f for f in os.listdir(folder) if f.lower().endswith(extensions)])
print(f"总共 {len(files)} 张")

for i, fname in enumerate(files, 1):
    path = os.path.join(folder, fname)
    img = read_image(path)
    if img is None:
        print(f"  {i}/{len(files)}  {fname}  ⚠️ 跳过")
        continue

    if fname == "1.png":
        # 参考图本身：只做轻度锐化
        sharpen = np.array([[-0.3, -0.3, -0.3],
                            [-0.3,  3.4, -0.3],
                            [-0.3, -0.3, -0.3]], dtype=np.float32)
        result = cv2.filter2D(img, -1, sharpen)
        save_image(path, result)
        kb = os.path.getsize(path) // 1024
        print(f"  {i}/{len(files)}  {fname}  → {kb}KB (参考图，轻度锐化)")
    else:
        # 其他图：匹配到 1.png 的风格
        result = match_style(img, ref_stats)
        save_image(path, result)
        kb = os.path.getsize(path) // 1024
        print(f"  {i}/{len(files)}  {fname}  → {kb}KB")

print("\n✅ 全部完成")
