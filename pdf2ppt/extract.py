"""
Stage 1 · PDF 内容提取
用 PyMuPDF 提取每页文字块（含坐标 bbox、字号、text_type）、嵌入图片、页面类型。
输出: comic_page_models.json
"""
import json
import hashlib
import argparse

import fitz


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def normalize_text_blocks(text_dict: dict) -> list[dict]:
    """PyMuPDF text dict → 干净文字块列表"""
    items = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines_text = []
        max_font_size = 0
        is_bold = False
        for line in block.get("lines", []):
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
                sz = span.get("size", 10)
                if sz > max_font_size:
                    max_font_size = sz
                if span.get("flags", 0) & 16:
                    is_bold = True
            lines_text.append(line_text)
        full_text = "".join(lines_text).strip()
        if not full_text:
            continue
        items.append({
            "text": full_text,
            "bbox": list(block["bbox"]),
            "font_size": round(max_font_size, 1),
            "is_bold": is_bold,
        })
    return items


def classify_text_items(text_items: list[dict], images: list[dict]) -> list[dict]:
    """标记每段文字类型: heading / body / dialogue / page_number"""
    page_h = 842
    for item in text_items:
        bbox = item["bbox"]
        y_center = (bbox[1] + bbox[3]) / 2
        text_len = len(item["text"])
        font_size = item.get("font_size", 10)

        if y_center < 40 or y_center > page_h - 40:
            item["text_type"] = "page_number"
            continue
        if font_size >= 18 and text_len < 50:
            item["text_type"] = "heading"
            continue
        if text_len < 80 and _nearby_image(bbox, images):
            item["text_type"] = "dialogue"
            continue
        item["text_type"] = "body"
    return text_items


def _nearby_image(text_bbox, images, threshold=120):
    ty = (text_bbox[1] + text_bbox[3]) / 2
    for img in images:
        iy = (img["bbox"][1] + img["bbox"][3]) / 2
        if abs(ty - iy) < threshold:
            return True
    return False


def extract_images(page, doc, min_dim=150):
    images = []
    cache = {}  # xref → (宽, 高, 后缀, 字节)：同一页重复引用同一图时避免重复解码
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        if xref in cache:
            w, h, ext, img_bytes = cache[xref]
        else:
            try:
                base = doc.extract_image(xref)
            except Exception:
                continue
            w, h, ext, img_bytes = base["width"], base["height"], base["ext"], base["image"]
            cache[xref] = (w, h, ext, img_bytes)
        if w < min_dim and h < min_dim:
            continue
        img_hash = md5(img_bytes)
        bboxes = _get_image_bboxes(page, img_info)
        for bbox in bboxes:
            images.append({
                "xref": xref,
                "bbox": list(bbox),
                "width": w,
                "height": h,
                "ext": ext,
                "md5": img_hash,
            })
    return images


def _get_image_bboxes(page, img_info):
    try:
        result = page.get_image_bbox(img_info)
        if result:
            if isinstance(result[0], (int, float)):
                return [list(result)]
            return [list(r) for r in result]
    except Exception:
        pass
    return [[0, 0, 0, 0]]


def detect_drawings(page):
    """检测矢量图（表格等）"""
    drawings = page.get_drawings()
    bboxes = []
    for d in drawings:
        rect = d["rect"]
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w > 150 and h > 80:
            bboxes.append(list(rect))
    return {"has_drawings": len(bboxes) > 0, "count": len(bboxes), "bboxes": bboxes}


def classify_page(text_items, images, has_drawings):
    text_count = len(text_items)
    img_count = len(images)
    total_len = sum(len(t["text"]) for t in text_items)

    if total_len < 80 and text_count <= 3:
        has_large = any(t.get("font_size", 10) >= 20 for t in text_items)
        if has_large or text_count <= 1:
            return "title_chapter"
    if total_len < 15 and img_count > 0:
        return "full_image"
    if img_count == 0:
        return "diagram" if has_drawings else "text_only"
    dialogue_count = sum(1 for t in text_items if t.get("text_type") == "dialogue")
    if img_count >= 1 and dialogue_count >= 1:
        return "comic"
    if has_drawings and img_count <= 2:
        return "diagram"
    return "mixed"


def extract_all_pages(pdf_path, min_img_dim=150, verbose=True):
    """提取 PDF 全部页面内容，返回 pages 列表"""
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_rect = list(page.rect)
        text_dict = page.get_text("dict")
        text_items = normalize_text_blocks(text_dict)
        images = extract_images(page, doc, min_dim=min_img_dim)
        text_items = classify_text_items(text_items, images)
        drawing_info = detect_drawings(page)
        page_type = classify_page(text_items, images, drawing_info["has_drawings"])

        pages.append({
            "page_num": page_num + 1,
            "page_rect": page_rect,
            "page_type": page_type,
            "text_items": text_items,
            "images": images,
            "drawings": drawing_info,
        })
        if verbose and (page_num + 1) % 20 == 0:
            print(f"  第 {page_num+1}/{doc.page_count} 页 [{page_type}]")

    doc.close()
    print(f"\n提取完成: {len(pages)} 页")
    return pages


def main():
    parser = argparse.ArgumentParser(description="Stage 1: 提取 PDF 内容")
    parser.add_argument("pdf", help="PDF 文件路径")
    parser.add_argument("-o", "--output", default="comic_page_models.json",
                        help="输出 JSON 路径")
    parser.add_argument("-s", "--min-size", type=int, default=150,
                        help="图片最小尺寸 px")
    args = parser.parse_args()

    pages = extract_all_pages(args.pdf, min_img_dim=args.min_size)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"已保存: {args.output}")


if __name__ == "__main__":
    main()
