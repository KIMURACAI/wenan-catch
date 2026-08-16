"""V2: Better text extraction - keep comic dialogue as part of content"""
import re, os, html as html_mod
from itertools import groupby

with open(r"e:\wenan catch\风水全书原文.txt", "r", encoding="utf-8") as f:
    raw = f.read()

pages = re.split(r'===== 第\d+页 =====', raw)
pages = [p.strip() for p in pages if p.strip()]
print(f"Pages: {len(pages)}")

# Clean each page
def clean_page(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            result.append('')
            continue
        if re.match(r'^\d{1,3}$', line):
            continue
        if len(line) <= 2:
            continue
        result.append(line)
    return '\n'.join(result)

clean_pages = [clean_page(p) for p in pages]

# Group into paragraphs: merge consecutive non-empty lines with space separator
def to_paragraphs(page_text):
    lines = page_text.split('\n')
    groups = groupby(lines, key=lambda x: x != '')
    paras = []
    for is_text, group in groups:
        if is_text:
            text = ' '.join(group)
            if len(text) > 20:
                paras.append(text)
    return paras

all_items = []  # list of (type, text) tuples
for i, p in enumerate(clean_pages):
    paras = to_paragraphs(p)
    for para in paras:
        all_items.append(para)

# Remove near-duplicates (fuzzy dedup)
seen = set()
unique_items = []
for item in all_items:
    # Normalize for dedup
    norm = re.sub(r'\s+', '', item)[:60]
    if norm not in seen:
        seen.add(norm)
        unique_items.append(item)

print(f"Unique paragraphs: {len(unique_items)}")
print(f"Total chars: {sum(len(p) for p in unique_items)}")

# Build slides
SLIDE_MAX = 500
slides_content = []
current = []
cc = 0
pending_header = None

for para in unique_items:
    is_h1 = bool(re.match(r'^[一二三四五六七八九十]、.{4,}', para))
    is_h2 = bool(re.match(r'^（[一二三四五六七八九十\d]+）', para))
    is_title = '中国传统风水学现代应用经典' in para

    if is_title:
        slides_content.append(['TITLE:' + para])
        continue

    # Start new slide on major headers
    if is_h1 and (cc > 100 or len(current) > 1):
        slides_content.append(current)
        current = []
        cc = 0

    current.append(para)
    cc += len(para)

    if cc > SLIDE_MAX:
        slides_content.append(current)
        current = []
        cc = 0

if current:
    slides_content.append(current)

print(f"Slides: {len(slides_content)}")

# === Build HTML ===
def tag(para):
    if para.startswith('TITLE:'):
        return 'title', para[6:]
    if re.match(r'^中国传统风水学现代应用经典', para):
        return 'title', para
    if '作者简介' in para or '成慈先生简介' in para:
        return 'h1', para
    if re.match(r'^[一二三四五六七八九十]、', para):
        return 'h1', para
    if re.match(r'^（[一二三四五六七八九十\d]+）', para):
        return 'h2', para
    if re.match(r'^\d+[、,.]', para) and len(para) < 80:
        return 'h3', para
    return 'p', para

def slide_html(idx, paragraphs):
    lines = []
    eyeb = ""

    for para in paragraphs:
        t, text = tag(para)
        text = html_mod.escape(text)

        if t == 'title':
            return f'''
<section class="slide cover">
  <h1>{text}</h1>
  <div class="divider"></div>
  <div class="sub">作者：成慈先生<br>茅山派第46代 · 吕祖蓬莱派第19代</div>
</section>'''

        if t == 'h1':
            lines.append(f'<h1>{text}</h1>')
            if not eyeb:
                eyeb = text[:50]
        elif t == 'h2':
            lines.append(f'<h2>{text}</h2>')
        elif t == 'h3':
            lines.append(f'<h3>{text}</h3>')
        else:
            lines.append(f'<p>{text}</p>')

    eb_html = f'<span class="eyebrow">{eyeb}</span>' if eyeb else ''
    return f'''
<section class="slide">
  {eb_html}
  {chr(10)+"  ".join(lines)}
  <div class="page-num">{idx+1}</div>
  <div class="footer-mark">中国传统风水学现代应用经典 · 成慈先生</div>
</section>'''

all_html = []
for i, sl in enumerate(slides_content):
    all_html.append(slide_html(i, sl))

css = '''<style>
  @page { size: 280mm 158mm; margin: 0; background: #f5f4ed; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --parchment:#f5f4ed; --near-black:#141413; --dark-warm:#3d3d3a;
    --olive:#504e49; --stone:#6b6a64; --brand:#1B365D; --border:#e0ddd2;
    --serif:"Source Han Serif SC","Noto Serif CJK SC","Songti SC","STSong","SimSun",serif;
  }
  body{color:var(--near-black);font-family:var(--serif);font-size:11pt;line-height:1.5;}
  .slide{width:280mm;height:158mm;padding:11mm 15mm;background:var(--parchment);break-after:page;position:relative;display:flex;flex-direction:column;}
  .slide:last-child{break-after:auto;}
  .eyebrow{font-size:7.5pt;letter-spacing:1.5pt;color:var(--stone);margin-bottom:1mm;}
  h1{font-size:19pt;font-weight:500;color:var(--near-black);border-left:3pt solid var(--brand);padding-left:8pt;margin-bottom:5pt;line-height:1.2;}
  h2{font-size:13pt;font-weight:500;color:var(--brand);margin:5pt 0 2pt 0;}
  h3{font-size:11pt;font-weight:500;color:var(--dark-warm);margin:3pt 0 2pt 0;}
  p{margin-bottom:2pt;font-size:10pt;line-height:1.4;text-indent:2em;}
  .page-num{position:absolute;bottom:7mm;right:15mm;font-size:7.5pt;color:var(--stone);}
  .footer-mark{position:absolute;bottom:7mm;left:15mm;font-size:7pt;color:var(--stone);letter-spacing:1pt;}
  .cover{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
  .cover h1{font-size:30pt;border:none;padding:0;letter-spacing:2pt;margin-bottom:10pt;}
  .cover .sub{font-size:12pt;color:var(--brand);line-height:1.6;}
  .cover .divider{width:35mm;height:1pt;background:var(--brand);margin-bottom:18pt;}
</style>'''

out = r"e:\wenan catch\风水课程-幻灯片.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(f'<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<title>中国传统风水学现代应用经典</title>\n{css}\n</head>\n<body>\n')
    f.write('\n'.join(all_html))
    f.write('\n</body>\n</html>')

print(f"Saved {len(all_html)} slides")
