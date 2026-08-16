"""
PDF 漫画/配图提取工具
从 PDF 中提取嵌入的图片，过滤掉过小的装饰元素和重复图片。
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict

import fitz  # PyMuPDF


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def extract_images(
    pdf_path: str,
    output_dir: str,
    min_dim: int = 300,
    dedup: bool = True,
    verbose: bool = True,
):
    """
    提取 PDF 中所有嵌入图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        min_dim: 最小尺寸阈值，宽或高小于此值的图片将被跳过
        dedup: 是否去重（相同 MD5 只保留一份）
        verbose: 是否输出详细信息
    """
    doc = fitz.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    # 统计
    stats = {
        "total_pages": doc.page_count,
        "total_images": 0,
        "skipped_small": 0,
        "skipped_dup": 0,
        "saved": 0,
    }

    seen_hashes = {}  # md5 -> (page_num, width, height)

    # 按页遍历
    for page_num in range(doc.page_count):
        page = doc[page_num]
        images = page.get_images()

        if not images:
            continue

        for img_idx, img in enumerate(images):
            stats["total_images"] += 1
            xref = img[0]

            try:
                base_image = doc.extract_image(xref)
            except Exception as e:
                if verbose:
                    print(f"  [跳过] 第{page_num+1}页 图片{img_idx+1}: 提取失败 ({e})")
                continue

            w = base_image["width"]
            h = base_image["height"]
            ext = base_image["ext"]
            img_bytes = base_image["image"]
            size_kb = len(img_bytes) / 1024

            # 过滤小图
            if w < min_dim and h < min_dim:
                stats["skipped_small"] += 1
                if verbose:
                    print(f"  [跳过-太小] 第{page_num+1}页 图片{img_idx+1}: {w}x{h} {ext} {size_kb:.0f}KB")
                continue

            # 去重
            img_hash = md5(img_bytes)
            if dedup and img_hash in seen_hashes:
                prev_info = seen_hashes[img_hash]
                stats["skipped_dup"] += 1
                if verbose:
                    print(f"  [跳过-重复] 第{page_num+1}页 图片{img_idx+1}: {w}x{h} → 与第{prev_info[0]}页相同")
                continue

            seen_hashes[img_hash] = (page_num + 1, w, h)

            # 生成文件名
            filename = f"p{page_num+1:03d}_{w}x{h}.{ext}"
            filepath = os.path.join(output_dir, filename)

            # 处理重名（不同页可能有相同尺寸不同内容的图）
            if os.path.exists(filepath):
                filename = f"p{page_num+1:03d}_{w}x{h}_{img_idx}.{ext}"
                filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(img_bytes)

            stats["saved"] += 1
            if verbose:
                print(f"  [保存] 第{page_num+1}页: {filename} ({size_kb:.0f}KB)")

    doc.close()

    # 输出统计
    print(f"\n{'='*50}")
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"总页数: {stats['total_pages']}")
    print(f"总图片数: {stats['total_images']}")
    print(f"  - 已保存: {stats['saved']}")
    print(f"  - 跳过(太小): {stats['skipped_small']}")
    print(f"  - 跳过(重复): {stats['skipped_dup']}")
    print(f"输出目录: {output_dir}")
    print(f"{'='*50}")

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取 PDF 中的漫画/配图")
    parser.add_argument("pdf", nargs="?", help="PDF 文件路径（默认：桌面待处理目录下的文件）")
    parser.add_argument(
        "-o", "--output",
        help="输出目录（默认：PDF 同目录下的 images 文件夹）",
    )
    parser.add_argument(
        "-s", "--min-size",
        type=int,
        default=300,
        help="最小尺寸阈值(px)，宽或高小于此值的跳过（默认: 300）",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="不去重，保留所有符合尺寸的图片",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="提取所有图片（包括小图和重复图）",
    )

    args = parser.parse_args()

    # 默认 PDF 路径：桌面待处理目录
    if args.pdf:
        pdf_path = args.pdf
    else:
        desktop_pending = Path.home() / "Desktop" / "待处理"
        pdfs = list(desktop_pending.glob("*.pdf"))
        if not pdfs:
            print("桌面待处理目录下没有 PDF 文件，请手动指定路径")
            sys.exit(1)
        pdf_path = str(pdfs[0])
        print(f"自动选择: {pdfs[0].name}")

    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    # 默认输出目录
    if args.output:
        output_dir = args.output
    else:
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(pdf_dir, f"{pdf_name}_images")

    extract_images(
        pdf_path=pdf_path,
        output_dir=output_dir,
        min_dim=args.min_size if not args.all else 0,
        dedup=not args.no_dedup and not args.all,
        verbose=True,
    )
