"""构建奇门遁甲预测案例课程 PPT (Kami 16:9 HTML → PDF)
来源: qimen_cases.json (由 extract_qimen.py 生成)
排盘表严格按源还原，表16已应用规则验证修正。"""
import json, html as H

JSON_PATH = r"e:\wenan catch\qimen_cases.json"
OUT_HTML = r"e:\wenan catch\奇门遁甲预测案例-课程.html"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

CSS = """<style>
@page { size: 280mm 158mm; margin: 0; background: #f5f4ed; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --parchment:#f5f4ed; --ivory:#faf9f5; --near-black:#141413; --dark-warm:#3d3d3a;
  --olive:#504e49; --stone:#6b6a64; --brand:#1B365D; --brand-tint:#EEF2F7; --border:#e0ddd2;
  --serif:"Source Han Serif SC","Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;
}
body{color:var(--near-black);font-family:var(--serif);font-size:11pt;line-height:1.55;}
.slide{width:280mm;height:158mm;padding:11mm 15mm;background:var(--parchment);break-after:page;position:relative;display:flex;flex-direction:column;}
.slide:last-child{break-after:auto;}
.eyebrow{font-size:8pt;letter-spacing:2pt;color:var(--brand);margin-bottom:1mm;}
h1{font-size:21pt;font-weight:500;color:var(--near-black);border-left:3pt solid var(--brand);padding-left:8pt;margin-bottom:4mm;line-height:1.25;}
p{margin-bottom:2mm;font-size:10.5pt;line-height:1.5;}
.page-num{position:absolute;bottom:7mm;right:15mm;font-size:8pt;color:var(--stone);}
.footer-mark{position:absolute;bottom:7mm;left:15mm;font-size:7pt;color:var(--stone);letter-spacing:1.5pt;}
.cover{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.cover h1{font-size:32pt;border:none;padding:0;letter-spacing:3pt;margin-bottom:8mm;}
.cover .sub{font-size:13pt;color:var(--brand);letter-spacing:2pt;margin-bottom:6mm;}
.cover .divider{width:40mm;height:1pt;background:var(--brand);margin-bottom:8mm;}
.cover .meta{font-size:10pt;color:var(--stone);line-height:1.8;}
.section-slide{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.section-slide .num{font-size:10pt;color:var(--stone);letter-spacing:2pt;margin-bottom:3mm;}
.section-slide h1{font-size:26pt;border:none;padding:0;color:var(--brand);margin-bottom:5mm;}
.info{font-size:9pt;color:var(--dark-warm);line-height:1.6;background:var(--ivory);border-left:2pt solid var(--brand);padding:2.5mm 4mm;margin-bottom:3mm;}
.info .row{margin-bottom:0.5mm;}
.chart-wrap{flex:1;display:flex;align-items:center;justify-content:center;}
table.qimen{border-collapse:collapse;margin:0 auto;table-layout:fixed;}
table.qimen td{border:0.6pt solid #c9c4b4;text-align:center;vertical-align:middle;width:62mm;height:26mm;padding:2mm 3mm;background:var(--ivory);}
table.qimen td.center{background:var(--brand-tint);}
.q-sp{font-size:7.5pt;color:var(--brand);letter-spacing:0.5pt;margin-bottom:0.5mm;}
.q-tg{font-size:16pt;font-weight:500;line-height:1.1;}
.q-dp{font-size:10pt;color:var(--dark-warm);margin-top:0.5mm;}
.q-ct{font-size:20pt;font-weight:500;color:var(--brand);}
.analysis-slide p{font-size:10.5pt;}
.close{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.close h1{font-size:24pt;border:none;padding:0;color:var(--brand);}
</style>"""


def esc(t):
    return H.escape(t)


def chart_html(grid, center):
    rows = []
    for ri in range(3):
        tds = []
        for ci in range(3):
            cell = grid[ri][ci]
            if cell["palace"] == 5:
                tds.append(f'<td class="center"><div class="q-ct">{esc(center)}</div></td>')
            else:
                tds.append(
                    f'<td>'
                    f'<div class="q-sp">{esc(cell["spirit"])}</div>'
                    f'<div class="q-tg">{esc(cell["tiangan"])}</div>'
                    f'<div class="q-dp">{esc(cell["dipan"])}</div>'
                    f"</td>"
                )
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return '<table class="qimen">' + "".join(rows) + "</table>"


slides = []
n = 0


def push(html):
    global n
    n += 1
    slides.append(f'<section class="slide">{html}<div class="page-num">{n}</div><div class="footer-mark">奇门遁甲预测案例精讲 · 成慈先生</div></section>')


def push_cover():
    slides.append(
        '<section class="slide cover">'
        '<h1>奇门遁甲<br>预测案例精讲</h1>'
        '<div class="divider"></div>'
        '<div class="sub">成慈老师 · 实战预测解析</div>'
        '<div class="meta">成慈高级奇门讲义 · 十二类预测 二十个案例<br>茅山派第46代 · 道教吕祖蓬莱派第19代</div>'
        "</section>"
    )
    global n
    n = 1


def push_section(title):
    global n
    n += 1
    slides.append(
        f'<section class="slide section-slide"><div class="num">奇门遁甲预测案例精讲</div><h1>{esc(title)}</h1>'
        f'<div class="page-num">{n}</div><div class="footer-mark">奇门遁甲预测案例精讲 · 成慈先生</div></section>'
    )


def split_content(paras, max_chars=600, max_items=6):
    groups, cur, cc = [], [], 0
    for p in paras:
        if cur and (cc + len(p) > max_chars or len(cur) >= max_items):
            groups.append(cur)
            cur, cc = [], 0
        cur.append(p)
        cc += len(p)
    if cur:
        groups.append(cur)
    return groups


def content_slide(section_eyebrow, title, paras, analysis=False):
    groups = split_content(paras)
    for gi, group in enumerate(groups):
        cls = "analysis-slide" if analysis else ""
        body = "".join(f"<p>{esc(p)}</p>" for p in group)
        suffix = f"（{gi + 1}）" if len(groups) > 1 else ""
        push(f'<span class="eyebrow">{esc(section_eyebrow)}</span><h1>{esc(title)}{suffix}</h1><div class="{cls}">{body}</div>')


def chart_slide(section_eyebrow, case):
    title = case["title"] or f"案例{case['index']}"
    info_html = "".join(f'<div class="row">{esc(h)}</div>' for h in case["header"])
    fix_note = ""
    for row in case["grid"]:
        for cell in row:
            if cell.get("fixed"):
                fix_note = f'<div class="row" style="color:#b3561B;">※ {esc(cell["fixed"])}</div>'
    push(
        f'<span class="eyebrow">{esc(section_eyebrow)}</span>'
        f'<h1>{esc(title)}</h1>'
        f'<div class="info">{info_html}{fix_note}</div>'
        f'<div class="chart-wrap">{chart_html(case["grid"], case["center"])}</div>'
    )


# ===== 封面 =====
push_cover()

# ===== 成慈老师简介 =====
push_section("成慈老师个人简介")
content_slide("成慈老师", "个人简介", data["preface"]["bio"])

# ===== 理论 / 分类节 =====
for s in data["sections"]:
    push_section(s["title"])
    if s["intro"]:
        content_slide("", s["title"], s["intro"])
    for case in s["cases"]:
        chart_slide(s["title"], case)
        if case["analysis"]:
            content_slide(s["title"], f"{case['title']} · 判断思路", case["analysis"], analysis=True)

# ===== 结尾 =====
slides.append(
    '<section class="slide close"><h1>福生无量 · 道法自然</h1>'
    '<div class="page-num"></div><div class="footer-mark">奇门遁甲预测案例精讲 · 成慈先生</div></section>'
)

html_doc = (
    '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
    f"<title>奇门遁甲预测案例精讲</title>\n{CSS}\n</head>\n<body>\n"
    + "\n".join(slides)
    + "\n</body>\n</html>"
)

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_doc)

print(f"生成 {OUT_HTML}: {len(slides)} 页")
