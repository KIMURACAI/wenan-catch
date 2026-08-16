#!/usr/bin/env python3
"""Generate standard Qimen Dunjia 九宫排盘图 as SVGs."""

import os
from xml.sax.saxutils import escape

# 九宫八卦方位
PALACES = {
    1: {"name": "坎", "pos": (2, 2), "direction": "北"},
    2: {"name": "坤", "pos": (2, 0), "direction": "西南"},
    3: {"name": "震", "pos": (0, 2), "direction": "东"},
    4: {"name": "巽", "pos": (0, 0), "direction": "东南"},
    5: {"name": "中", "pos": (1, 1), "direction": "中"},
    6: {"name": "乾", "pos": (2, 1), "direction": "西北"},
    7: {"name": "兑", "pos": (1, 0), "direction": "西"},
    8: {"name": "艮", "pos": (0, 1), "direction": "东北"},
    9: {"name": "离", "pos": (1, 2), "direction": "南"},
}

# 洛书数位置 (row, col), 0-indexed
LUOSHU = {
    4: (0, 0), 9: (0, 1), 2: (0, 2),  # 巽 离 坤
    3: (1, 0), 5: (1, 1), 7: (1, 2),  # 震 中 兑
    8: (2, 0), 1: (2, 1), 6: (2, 2),  # 艮 坎 乾
}

PALACE_NAMES = {
    4: "巽", 9: "离", 2: "坤",
    3: "震", 5: "中", 7: "兑",
    8: "艮", 1: "坎", 6: "乾",
}

DIRECTIONS = {
    4: "东南", 9: "南", 2: "西南",
    3: "东", 5: "中", 7: "西",
    8: "东北", 1: "北", 6: "西北",
}

CELL_W = 140
CELL_H = 140
GAP = 0
MARGIN = 20
WIDTH = 3 * CELL_W + 4 * GAP + 2 * MARGIN
HEIGHT = 3 * CELL_H + 4 * GAP + 2 * MARGIN

def make_chart(cells, title="", subtitle=""):
    """Create a Qimen 九宫格 SVG.
    cells: dict mapping  palace_num -> {
        'shen': '值符',     # 八神
        'men': '休门',      # 八门
        'xing': '天蓬',     # 九星
        'tian': '戊',       # 天盘干
        'di': '癸',         # 地盘干
        'extra': ''         # extra info
    }
    """
    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT + 60}" width="100%" height="100%">
    <defs>
        <style>
            .bg {{ fill: #faf9f5; }}
            .cell-bg {{ fill: #f5f4ed; stroke: #1B365D; stroke-width: 1.5; }}
            .cell-bg-center {{ fill: #e8e6dc; stroke: #1B365D; stroke-width: 1.5; }}
            .title {{ font-family: 'Georgia', 'SimSun', serif; font-size: 18px; fill: #1B365D; font-weight: bold; }}
            .subtitle {{ font-family: 'Georgia', 'SimSun', serif; font-size: 13px; fill: #5a5a55; }}
            .dir-label {{ font-family: 'Georgia', 'SimSun', serif; font-size: 11px; fill: #8a8a85; }}
            .palace-name {{ font-family: 'Georgia', 'SimSun', serif; font-size: 14px; fill: #1B365D; font-weight: bold; }}
            .shen {{ font-family: 'Georgia', 'SimSun', serif; font-size: 12px; fill: #8B0000; }}  /* 八神-红色 */
            .xing {{ font-family: 'Georgia', 'SimSun', serif; font-size: 11px; fill: #1B365D; }}  /* 九星-蓝色 */
            .men {{ font-family: 'Georgia', 'SimSun', serif; font-size: 11px; fill: #2D5A8A; }}
            .gan {{ font-family: 'Georgia', 'SimSun', serif; font-size: 16px; fill: #000000; font-weight: bold; }}
            .di-gan {{ font-family: 'Georgia', 'SimSun', serif; font-size: 11px; fill: #666660; }}
            .extra {{ font-family: 'Georgia', 'SimSun', serif; font-size: 10px; fill: #8a8a85; }}
            .legend {{ font-family: 'Georgia', 'SimSun', serif; font-size: 10px; fill: #5a5a55; }}
        </style>
    </defs>
    <rect class="bg" width="100%" height="100%" />
    ''')

    # Title
    if title:
        svg_parts.append(f'<text class="title" x="{MARGIN}" y="30">{escape(title)}</text>')
    if subtitle:
        svg_parts.append(f'<text class="subtitle" x="{MARGIN}" y="50">{escape(subtitle)}</text>')

    # 方位标签
    dir_labels = {
        (0, 1): "南", (2, 1): "北",
        (1, 0): "西", (1, 2): "东",
    }
    y0 = MARGIN + 60

    for palace_num, (row, col) in LUOSHU.items():
        x = MARGIN + col * (CELL_W + GAP)
        y = y0 + row * (CELL_H + GAP)
        cx = x + CELL_W // 2
        cy = y + CELL_H // 2

        is_center = (palace_num == 5)
        cls = "cell-bg-center" if is_center else "cell-bg"

        svg_parts.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="2" />')

        # Direction label on top-left
        dir_name = DIRECTIONS[palace_num]
        svg_parts.append(f'<text class="dir-label" x="{x + 4}" y="{y + 12}">{escape(dir_name)}</text>')

        # Palace name on top-right
        pname = PALACE_NAMES[palace_num]
        svg_parts.append(f'<text class="palace-name" text-anchor="end" x="{x + CELL_W - 4}" y="{y + 14}">{escape(pname)}</text>')

        if palace_num in cells:
            c = cells[palace_num]
            # 八神 - top
            svg_parts.append(f'<text class="shen" text-anchor="middle" x="{cx}" y="{y + 28}">{escape(c.get("shen", ""))}</text>')
            # 天盘干 - center big
            svg_parts.append(f'<text class="gan" text-anchor="middle" x="{cx}" y="{y + 65}">{escape(c.get("tian", ""))}</text>')
            # 地盘干 - bottom right small
            svg_parts.append(f'<text class="di-gan" text-anchor="end" x="{x + CELL_W - 6}" y="{y + CELL_H - 6}">{escape(c.get("di", ""))}</text>')
            # 九星 - left
            svg_parts.append(f'<text class="xing" x="{x + 6}" y="{y + 50}">{escape(c.get("xing", ""))}</text>')
            # 八门 - right
            svg_parts.append(f'<text class="men" text-anchor="end" x="{x + CELL_W - 6}" y="{y + 50}">{escape(c.get("men", ""))}</text>')
            # Extra
            if c.get("extra"):
                svg_parts.append(f'<text class="extra" text-anchor="middle" x="{cx}" y="{y + 85}">{escape(c["extra"])}</text>')
        else:
            # Empty center palace
            pass

    # Legend footer
    legend_y = y0 + 3 * CELL_H + 30
    legend_items = [
        ("八神", "#8B0000"), ("九星", "#1B365D"), ("八门", "#2D5A8A"),
        ("天盘干", "#000000"), ("地盘干", "#666660")
    ]
    lx = MARGIN
    for i, (text, color) in enumerate(legend_items):
        svg_parts.append(f'<rect x="{lx}" y="{legend_y}" width="10" height="10" fill="{color}" opacity="0.7" />')
        svg_parts.append(f'<text class="legend" x="{lx + 14}" y="{legend_y + 10}">{escape(text)}</text>')
        lx += 60

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


# ===== Example 1: 阴遁5局 庚午时 (演局篇主例) =====
cells_ex1 = {
    4: {"shen": "太阴", "xing": "天辅", "men": "杜门", "tian": "癸", "di": "己"},
    9: {"shen": "螣蛇", "xing": "天英", "men": "景门", "tian": "己", "di": "癸"},
    2: {"shen": "值符", "xing": "天芮禽", "men": "死门", "tian": "辛", "di": "辛"},
    3: {"shen": "六合", "xing": "天冲", "men": "伤门", "tian": "壬", "di": "丁"},
    5: {"shen": "", "xing": "天禽", "men": "", "tian": "戊", "di": "戊"},
    7: {"shen": "九天", "xing": "天柱", "men": "惊门", "tian": "庚", "di": "庚"},
    8: {"shen": "九地", "xing": "天任", "men": "生门", "tian": "丁", "di": "壬"},
    1: {"shen": "玄武", "xing": "天蓬", "men": "休门", "tian": "丙", "di": "乙"},
    6: {"shen": "白虎", "xing": "天心", "men": "开门", "tian": "乙", "di": "丙"},
}

# ===== Example 2: 阳7局 己未时 (五不遇时) =====
cells_ex2 = {
    4: {"shen": "太阴", "xing": "天英", "men": "景门", "tian": "庚", "di": "丁", "extra": "马"},
    9: {"shen": "六合", "xing": "天芮禽", "men": "死门", "tian": "壬", "di": "癸"},
    2: {"shen": "白虎", "xing": "天柱", "men": "惊门", "tian": "戊", "di": "己"},
    3: {"shen": "螣蛇", "xing": "天辅", "men": "杜门", "tian": "丁", "di": "庚"},
    5: {"shen": "", "xing": "天禽", "men": "", "tian": "癸", "di": "癸"},
    7: {"shen": "玄武", "xing": "天心", "men": "开门", "tian": "乙", "di": "戊"},
    8: {"shen": "值符", "xing": "天冲", "men": "伤门", "tian": "己", "di": "壬", "extra": "○"},
    1: {"shen": "九天", "xing": "天任", "men": "生门", "tian": "辛", "di": "乙"},
    6: {"shen": "九地", "xing": "天蓬", "men": "休门", "tian": "丙", "di": "辛"},
}

# ===== Example 3: 阴9局 癸未时 (投资例) =====
cells_ex3 = {
    4: {"shen": "值符", "xing": "天任", "men": "杜门", "tian": "己", "di": "癸", "extra": "马"},
    9: {"shen": "九天", "xing": "天冲", "men": "景门", "tian": "丁", "di": "戊"},
    2: {"shen": "九地", "xing": "天辅", "men": "死门", "tian": "癸", "di": "丙"},
    3: {"shen": "螣蛇", "xing": "天蓬", "men": "伤门", "tian": "乙", "di": "丁"},
    5: {"shen": "", "xing": "天禽", "men": "", "tian": "壬", "di": "壬"},
    7: {"shen": "玄武", "xing": "天英", "men": "惊门", "tian": "戊", "di": "庚"},
    8: {"shen": "太阴", "xing": "天心", "men": "生门", "tian": "辛", "di": "己"},
    1: {"shen": "六合", "xing": "天柱", "men": "休门", "tian": "庚", "di": "乙"},
    6: {"shen": "白虎", "xing": "天芮禽", "men": "开门", "tian": "丙", "di": "辛"},
}

# ===== Example 4: 阳8局 戊午时 (阴宅例) =====
cells_ex4 = {
    4: {"shen": "太阴", "xing": "天芮禽", "men": "死门", "tian": "辛", "di": "癸"},
    9: {"shen": "六合", "xing": "天柱", "men": "惊门", "tian": "乙", "di": "己"},
    2: {"shen": "白虎", "xing": "天心", "men": "开门", "tian": "丙", "di": "辛"},
    3: {"shen": "螣蛇", "xing": "天英", "men": "景门", "tian": "己", "di": "壬"},
    5: {"shen": "", "xing": "天禽", "men": "", "tian": "丁", "di": "丁"},
    7: {"shen": "玄武", "xing": "天蓬", "men": "休门", "tian": "庚", "di": "乙"},
    8: {"shen": "值符", "xing": "天辅", "men": "杜门", "tian": "癸", "di": "戊"},
    1: {"shen": "九天", "xing": "天冲", "men": "伤门", "tian": "壬", "di": "庚"},
    6: {"shen": "九地", "xing": "天任", "men": "生门", "tian": "戊", "di": "丙"},
}


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    charts = [
        ("阴遁5局_庚午时", cells_ex1, "阴遁5局 庚午时", "2010年11月25日12:06"),
        ("阳7局_己未时", cells_ex2, "阳遁7局 己未时", "2009年12月24日14:51·五不遇时"),
        ("阴9局_癸未时", cells_ex3, "阴遁9局 癸未时", "2010年6月29日13:06·投资例"),
        ("阳8局_戊午时", cells_ex4, "阳遁8局 戊午时", "2010年4月28日12:42·阴宅例"),
    ]
    for fname, cells, title, sub in charts:
        svg = make_chart(cells, title=title, subtitle=sub)
        path = os.path.join(out_dir, f"qimen_{fname}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Created: {path}")
    print("Done! 4 charts generated.")
