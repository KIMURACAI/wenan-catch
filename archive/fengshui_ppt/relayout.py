"""
重排版 PPT：拉伸图片填满页面、提高填充度
- 不动文字内容、不增删
- 只缩放图片尺寸（保持宽高比，不裁剪）
- 标准图文页：图片填满左半页，正文保持右侧
- 特殊页单独处理
"""
from pptx import Presentation
from pptx.util import Pt, Emu

prs = Presentation(r'e:\wenan catch\output_final.pptx')
SLIDE_W = 12188952
SLIDE_H = 6858000

# 左半页可用区域
IMG_AREA_LEFT = Emu(914400 * 0.3)
IMG_AREA_TOP = Emu(914400 * 0.7)
IMG_AREA_W = Emu(914400 * 6.9)
IMG_AREA_H = Emu(914400 * 6.4)

# 特殊页：目录页（图已大，保持）、横排图页
SKIP_SLIDES = {2, 73}  # Slide 2=目录, 73=横排三图


def fit_and_place(img, area_left, area_top, area_w, area_h):
    """保持宽高比缩放到区域内，居中"""
    iw, ih = img.width, img.height
    if iw == 0 or ih == 0:
        return
    scale = min(area_w / iw, area_h / ih) * 0.97
    nw = int(iw * scale)
    nh = int(ih * scale)
    nx = area_left + (area_w - nw) // 2
    ny = area_top + (area_h - nh) // 2
    img.left = nx
    img.top = ny
    img.width = nw
    img.height = nh


def find_text_left(slide):
    """找右侧正文框左边界"""
    text_left_min = SLIDE_W
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            if sh.left / 914400 > 4.5:
                text_left_min = min(text_left_min, sh.left)
    return text_left_min


def process_standard(slide):
    """标准左图右文页"""
    imgs = [sh for sh in slide.shapes if sh.shape_type == 13]
    if not imgs:
        return

    text_left = find_text_left(slide)
    avail_right = min(text_left - Emu(914400 * 0.3), Emu(914400 * 7.2))
    area_w = max(avail_right - IMG_AREA_LEFT, Emu(914400 * 3))

    n = len(imgs)
    if n == 1:
        fit_and_place(imgs[0], IMG_AREA_LEFT, IMG_AREA_TOP, area_w, IMG_AREA_H)
    elif n == 2:
        gap = Emu(914400 * 0.2)
        half_h = (IMG_AREA_H - gap) // 2
        fit_and_place(imgs[0], IMG_AREA_LEFT, IMG_AREA_TOP, area_w, half_h)
        fit_and_place(imgs[1], IMG_AREA_LEFT, IMG_AREA_TOP + half_h + gap, area_w, half_h)
    else:
        gap = Emu(914400 * 0.15)
        cols = 2
        rows = (n + 1) // 2
        cell_w = (area_w - gap) // cols
        cell_h = (IMG_AREA_H - gap * (rows - 1)) // rows
        for i, img in enumerate(imgs[:4]):
            col = i % cols
            row = i // cols
            fit_and_place(img, IMG_AREA_LEFT + col * (cell_w + gap),
                          IMG_AREA_TOP + row * (cell_h + gap), cell_w, cell_h)


def process_special_147(slide):
    """图表页（窄长图）：放大到左半页全高"""
    imgs = [sh for sh in slide.shapes if sh.shape_type == 13]
    for img in imgs:
        fit_and_place(img, IMG_AREA_LEFT, IMG_AREA_TOP, IMG_AREA_W, IMG_AREA_H)


def process_slide(slide, snum):
    if snum in SKIP_SLIDES:
        return
    imgs = [sh for sh in slide.shapes if sh.shape_type == 13]
    if not imgs:
        return

    # 判断是否为图表页（图窄长：宽高比 > 0.5，且只有一张）
    if snum >= 147:
        process_special_147(slide)
    else:
        process_standard(slide)


def main():
    for snum, slide in enumerate(prs.slides, 1):
        process_slide(slide, snum)

    prs.save(r'e:\wenan catch\output_final.pptx')
    print(f"重排版完成: {len(prs.slides)} 页")
    print(f"跳过: {SKIP_SLIDES}")


if __name__ == "__main__":
    main()
