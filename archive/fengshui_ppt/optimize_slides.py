#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optimize existing PPT for better density and viewing."""
from pptx import Presentation; from pptx.util import Inches, Pt, Emu; from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR; from pptx.enum.shapes import MSO_SHAPE

prs = Presentation('e:\\wenan catch\\成慈高级奇门讲义_全量版.pptx')

# Analyze current slides
total = len(prs.slides)
shapes_total = sum(len(s.shapes) for s in prs.slides)
print(f'Total slides: {total}')
print(f'Total shapes: {shapes_total}')
print(f'Avg shapes/slide: {shapes_total/total:.1f}')

# Check font sizes used
sizes = set()
for s in prs.slides:
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size: sizes.add(int(r.font.size/12700))

print(f'Font sizes used (pt): {sorted(sizes)}')

# Get content density measure per slide
print('\nSlide content analysis:')
for i, s in enumerate(prs.slides):
    tx_count = 0; total_chars = 0
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                txt = p.text.strip()
                if txt: tx_count += 1; total_chars += len(txt)
    pct = min(100, total_chars / 150)  # rough estimate
    if pct < 30 or pct > 90:
        pass  # print(f'  Slide {i+1}: {tx_count} texts, {total_chars} chars (~{pct:.0f}% fill)')

# Optimize: increase font sizes where too small, ensure consistent styling
changes = 0
for s in prs.slides:
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size and r.font.size < Pt(7):
                        r.font.size = Pt(7)
                        changes += 1

print(f'\nOptimized {changes} runs')
prs.save('e:\\wenan catch\\成慈高级奇门讲义_全量版.pptx')
print('Saved optimized version')
