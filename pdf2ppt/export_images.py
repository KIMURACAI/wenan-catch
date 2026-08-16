"""
Stage 2 前置 · 导出 PDF 内嵌图片
无用户手裁图时，把 PDF 内嵌图导出为 _user_images/slide{NNN}_imgNN.ext，
与手裁图同一命名约定，build_ppt 自动使用。用户日后可同名替换为手裁高清图。
"""
import json, os
import fitz


def has_user_images(img_dir):
    """是否已有用户手裁图（slide{NNN}_img*）"""
    if not os.path.isdir(img_dir):
        return False
    for fname in os.listdir(img_dir):
        if fname.startswith('slide') and fname.endswith(('.png', '.jpg', '.jpeg')):
            return True
    return False


def export_embedded(pdf_path, page_json, out_dir, verbose=True):
    """导出 PDF 内嵌图（按页去重）到 out_dir，命名 slide{pn+1:03d}_img{NN}.ext"""
    pages = json.load(open(page_json, 'r', encoding='utf-8'))
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    count = 0
    for page in pages:
        pn = page['page_num']
        seen = set()
        idx = 0
        for im in page.get('images', []):
            if im.get('md5') in seen:
                continue
            seen.add(im['md5'])
            try:
                base = doc.extract_image(im['xref'])
            except Exception:
                continue
            idx += 1
            fname = f"slide{pn+1:03d}_img{idx:02d}.{base['ext']}"
            with open(os.path.join(out_dir, fname), 'wb') as f:
                f.write(base['image'])
            count += 1
    doc.close()
    if verbose:
        print(f"已导出 {count} 张内嵌图 → {out_dir}")
    return count
