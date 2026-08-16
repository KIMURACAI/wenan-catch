"""
古籍手写截图 → 白纸黑字扫描件
依赖: pip install opencv-python numpy
用法: python 古籍扫描件.py <图片路径> [模式]
  模式: auto  自动均衡 (默认, 适合大多数)
        hard  强力去黄/去背景 (适合深黄旧纸)
        soft  轻柔处理 (适合墨色较淡的)
        clean 纯黑白二值 (极致清晰)
"""

import cv2
import numpy as np
import sys
import os
from pathlib import Path


def load_image(path):
    """支持中文路径的图片读取"""
    with open(path, "rb") as f:
        data = f.read()
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        print(f"❌ 无法读取图片: {path}")
        sys.exit(1)
    return img


def save_result(img, src_path, suffix, out_dir=None):
    """支持中文路径的图片保存"""
    p = Path(src_path)
    if out_dir:
        out = Path(out_dir) / f"{p.stem}_{suffix}{p.suffix}"
    else:
        out = p.parent / f"{p.stem}_{suffix}{p.suffix}"
    # 使用 imencode 写文件以支持中文路径
    success, encoded = cv2.imencode(f".{p.suffix}", img)
    if not success:
        print(f"❌ 编码失败: {p.suffix}")
        sys.exit(1)
    with open(str(out), "wb") as f:
        f.write(encoded.tobytes())
    print(f"✅ 已保存: {out}")
    return out


def mode_auto(img):
    """自动均衡模式：CLAHE + 自适应阈值，适合大多数古籍"""
    # 1. 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. CLAHE 局部对比度均衡 (消除光照不均)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # 3. 轻微降噪 (保留笔画边缘)
    denoised = cv2.fastNlMeansDenoising(equalized, h=5, templateWindowSize=7, searchWindowSize=21)

    # 4. 自适应阈值 (处理局部明暗变化)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=15, C=5
    )

    # 5. 白纸着色 (暖白背景)
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    # 将白色(255)替换为暖白 #F5F0E8
    mask_white = binary == 255
    result[mask_white] = [232, 240, 245]  # BGR: 暖白
    # 将黑色(0)加深为纯黑
    result[~mask_white] = [30, 30, 30]    # BGR: 极深灰，比纯黑柔和

    return result, binary


def mode_hard(img):
    """强力去黄模式：针对深黄/深色旧纸"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 强 CLAHE
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # 2. 中值滤波去噪
    denoised = cv2.medianBlur(equalized, 3)

    # 3. OTSU 二值化 (全局最佳阈值)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. 形态学: 去除小噪点
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 5. 白纸着色
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    result[binary == 255] = [240, 245, 250]  # 暖白
    result[binary == 0]   = [25, 25, 25]     # 近黑

    return result, binary


def mode_soft(img):
    """轻柔模式：适合墨色较淡、笔画纤细的手写"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 弱 CLAHE，不过度增强
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # 2. 双边滤波 (保留边缘去噪)
    denoised = cv2.bilateralFilter(equalized, d=7, sigmaColor=30, sigmaSpace=30)

    # 3. 较小的 blockSize 保留细节
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, blockSize=11, C=3
    )

    # 4. 暖白背景
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    result[binary == 255] = [238, 242, 248]
    result[binary == 0]   = [35, 35, 35]

    return result, binary


def mode_clean(img):
    """纯黑白二值模式：极致清晰，专为阅读优化"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. CLAHE
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray)

    # 2. 高斯模糊去噪
    blurred = cv2.GaussianBlur(equalized, (3, 3), 0)

    # 3. OTSU 二值
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. 去小白点
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # 5. 纯白纯黑
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    result[binary == 255] = [255, 255, 255]
    result[binary == 0]   = [0, 0, 0]

    return result, binary


def show_preview(original, result, binary):
    """并排显示前后对比"""
    h1, w1 = original.shape[:2]
    h2, w2 = result.shape[:2]
    # 缩放到统一高度
    target_h = 800
    scale1 = target_h / h1
    scale2 = target_h / h2
    prev_orig = cv2.resize(original, (int(w1 * scale1), target_h))
    prev_result = cv2.resize(result, (int(w2 * scale2), target_h))

    # 并排
    comparison = np.hstack([prev_orig, prev_result])
    cv2.imshow("原图 (左)  ←  处理后 (右)  |  按 ESC 关闭", comparison)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    if len(sys.argv) < 2:
        print("用法: python 古籍扫描件.py <图片路径> [模式] [输出目录]")
        print("  模式: auto  - 自动均衡 (默认)")
        print("        hard  - 强力去黄")
        print("        soft  - 轻柔保留")
        print("        clean - 纯黑白二值")
        print("  输出目录: 可选，默认与原图同目录")
        sys.exit(1)

    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "auto"
    out_dir = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"📖 处理: {path}")
    print(f"🔧 模式: {mode}")
    if out_dir:
        print(f"📂 输出: {out_dir}")

    img = load_image(path)
    print(f"📐 尺寸: {img.shape[1]}x{img.shape[0]}")

    modes = {
        "auto": mode_auto,
        "hard": mode_hard,
        "soft": mode_soft,
        "clean": mode_clean,
    }

    if mode not in modes:
        print(f"❌ 未知模式: {mode}，可选: auto, hard, soft, clean")
        sys.exit(1)

    result, binary = modes[mode](img)

    # 保存 (与原件同格式 PNG)
    save_result(result, path, f"scan_{mode}", out_dir)

    # 尝试显示预览 (如无 GUI 则跳过)
    try:
        show_preview(img, result, binary)
    except cv2.error:
        print("💡 提示: 当前环境无 GUI 支持，预览已跳过")


if __name__ == "__main__":
    main()
