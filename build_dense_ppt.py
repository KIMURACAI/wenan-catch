#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact high-density Qimen PPT ~35 slides."""
from pptx import Presentation; from pptx.util import Inches, Pt; from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN; from pptx.enum.shapes import MSO_SHAPE
C=lambda n:RGBColor(*n)
IB=(0x1B,0x36,0x5D); IL=(0x2D,0x5A,0x8A); PC=(0xF5,0xF4,0xED); IV=(0xFA,0xF9,0xF5)
DT=(0x1A,0x1A,0x18); BT=(0x33,0x33,0x30); RA=(0x8B,0x00,0x00); WH=(0xFF,0xFF,0xFF)
WG=(0x5A,0x5A,0x55); OR=(0xCC,0x66,0x00); B2=(0xEE,0xF2,0xF7); BD=(0xE8,0xE6,0xDC)
prs=Presentation(); prs.slide_width=Inches(13.33); prs.slide_height=Inches(7.5)
B=Inches(0.4); SW=Inches(13.33); SH=Inches(7.5)
def ns():
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid()
    s.background.fill.fore_color.rgb=C(PC); return s
def tx(s,l,t,w,h,txt,sz=11,c=None,b=False,a=PP_ALIGN.LEFT):
    c=c or C(BT); bx=s.shapes.add_textbox(l,t,w,h); bx.text_frame.word_wrap=True
    p=bx.text_frame.paragraphs[0]; p.text=str(txt); p.font.size=Pt(sz)
    p.font.color.rgb=c; p.font.bold=b; p.alignment=a
def bg(s,t,sub=''):
    bx=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SW,Inches(0.55))
    bx.fill.solid(); bx.fill.fore_color.rgb=C(IB); bx.line.fill.background()
    tx(s,B,Inches(0.04),Inches(9),Inches(0.47),t,20,c=C(WH),b=True)
    if sub: tx(s,Inches(9),Inches(0.08),Inches(4),Inches(0.4),sub,10,c=RGBColor(0xBB,0xBB,0xCC))
def rn(s,l,t,w,h,fi=None,bo=None):
    r=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,l,t,w,h)
    r.fill.solid(); r.fill.fore_color.rgb=fi or C(IV); r.line.color.rgb=bo or C(BD); r.line.width=Pt(0.5)
def gc(s,cl,l=Inches(0.15),t=Inches(0.65),sz=Inches(3.8)):
    po={4:(0,0),9:(0,1),2:(0,2),3:(1,0),5:(1,1),7:(1,2),8:(2,0),1:(2,1),6:(2,2)}
    pd={4:'东南',9:'南',2:'西南',3:'东',5:'',7:'西',8:'东北',1:'北',6:'西北'}
    pn={1:'坎',2:'坤',3:'震',4:'巽',5:'中',6:'乾',7:'兑',8:'艮',9:'离'}
    cw=int(sz/3); ch=int(sz/3)
    for nu,(r,c) in po.items():
        x=int(l+c*cw); y=int(t+r*ch)
        rx=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x,y,cw,ch)
        rx.fill.solid(); rx.fill.fore_color.rgb=RGBColor(0xE8,0xE6,0xDC) if nu==5 else C(IV)
        rx.line.color.rgb=C(IB); rx.line.width=Pt(0.8)
        tx(s,x+2,y+1,int(cw*0.4),int(ch*0.12),pd[nu],5,c=C(WG))
        tx(s,x+int(cw*0.6),y+1,int(cw*0.38),int(ch*0.12),pn[nu],6,c=C(IB),b=True,a=PP_ALIGN.RIGHT)
        if nu in cl:
            d=cl[nu]
            if d[0]: tx(s,x+2,y+int(ch*0.12),cw-4,int(ch*0.14),d[0],6,c=C(RA),a=PP_ALIGN.CENTER)
            tx(s,x,y+int(ch*0.30),cw,int(ch*0.28),d[3],13,c=C(DT),b=True,a=PP_ALIGN.CENTER)
            tx(s,x+2,y+int(ch*0.68),int(cw*0.4),int(ch*0.12),d[1],5,c=C(IB))
            tx(s,x+int(cw*0.55),y+int(ch*0.68),int(cw*0.43),int(ch*0.12),d[2],5,c=C(IL),a=PP_ALIGN.RIGHT)
            tx(s,x+int(cw*0.6),y+int(ch*0.82),int(cw*0.38),int(ch*0.12),d[4],5,c=C(WG),a=PP_ALIGN.RIGHT)
            if d[5]: tx(s,x+2,y+int(ch*0.55),cw-4,int(ch*0.12),d[5],5,c=C(OR),a=PP_ALIGN.CENTER)

YN5={4:('太阴','天辅','杜门','癸','己',''),9:('螣蛇','天英','景门','己','癸',''),2:('值符','天芮禽','死门','辛','辛',''),3:('六合','天冲','伤门','壬','丁',''),5:('','天禽','','戊','戊',''),7:('九天','天柱','惊门','庚','庚',''),8:('九地','天任','生门','丁','壬',''),1:('玄武','天蓬','休门','丙','乙',''),6:('白虎','天心','开门','乙','丙','')}
Y9={4:('值符','天任','杜门','己','癸','马'),9:('九天','天冲','景门','丁','戊',''),2:('九地','天辅','死门','癸','丙',''),3:('螣蛇','天蓬','伤门','乙','丁',''),5:('','天禽','','壬','壬',''),7:('玄武','天英','惊门','戊','庚',''),8:('太阴','天心','生门','辛','己',''),1:('六合','天柱','休门','庚','乙',''),6:('白虎','天芮禽','开门','丙','辛','')}
Y8={4:('太阴','天芮禽','死门','辛','癸',''),9:('六合','天柱','惊门','乙','己',''),2:('白虎','天心','开门','丙','辛',''),3:('螣蛇','天英','景门','己','壬',''),5:('','天禽','','丁','丁',''),7:('玄武','天蓬','休门','庚','乙',''),8:('值符','天辅','杜门','癸','戊',''),1:('九天','天冲','伤门','壬','庚',''),6:('九地','天任','生门','戊','丙','')}
