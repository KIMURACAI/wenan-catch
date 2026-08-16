#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate comprehensive Qimen Dunjia PPT (~90+ slides)."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Colors
IB = RGBColor(0x1B,0x36,0x5D); IL = RGBColor(0x2D,0x5A,0x8A)
PC = RGBColor(0xF5,0xF4,0xED); IV = RGBColor(0xFA,0xF9,0xF5)
BD = RGBColor(0xE8,0xE6,0xDC); DT = RGBColor(0x1A,0x1A,0x18)
BT = RGBColor(0x33,0x33,0x30); RA = RGBColor(0x8B,0x00,0x00)
WH = RGBColor(0xFF,0xFF,0xFF); WG = RGBColor(0x5A,0x5A,0x55)
OR = RGBColor(0xCC,0x66,0x00)

W = Inches(13.33); H = Inches(7.5)
prs = Presentation(); prs.slide_width = W; prs.slide_height = H

def bg(s,c=PC):
    f=s.background.fill; f.solid(); f.fore_color.rgb=c

def tb(s,l,t,w,h,txt,sz=11,c=BT,b=False,a=PP_ALIGN.LEFT):
    bx=s.shapes.add_textbox(l,t,w,h); tf=bx.text_frame; tf.word_wrap=True
    p=tf.paragraphs[0]; p.text=str(txt); p.font.size=Pt(sz); p.font.color.rgb=c; p.font.bold=b; p.alignment=a
    return bx

def bar(s,t,sub=''):
    bx=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,W,Inches(0.6))
    bx.fill.solid(); bx.fill.fore_color.rgb=IB; bx.line.fill.background()
    tb(s,Inches(0.4),Inches(0.05),Inches(12),Inches(0.5),t,sz=20,c=WH,b=True)
    if sub: tb(s,Inches(6),Inches(0.08),Inches(7),Inches(0.4),sub,sz=11,c=RGBColor(0xBB,0xBB,0xCC))
    return bx

def bd(s,it,top=Inches(0.8),left=Inches(0.4),w=Inches(12.5),sz=9):
    bx=s.shapes.add_textbox(left,top,w,Inches(5.8)); tf=bx.text_frame; tf.word_wrap=True
    for i,itm in enumerate(it):
        if isinstance(itm,str): t,lv,b,c,sz2=itm,0,False,BT,sz
        else: t=itm[0]; lv=itm[1] if len(itm)>1 else 0; b=itm[2] if len(itm)>2 else False; c=itm[3] if len(itm)>3 else BT; sz2=itm[4] if len(itm)>4 else sz
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=str(t); p.font.size=Pt(max(6,sz2-lv)); p.font.bold=b; p.font.color.rgb=c; p.level=lv; p.space_after=Pt(2)

def ns():
    s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s); return s

def ts(t,sub,it):
    s=ns(); bar(s,t,sub); bd(s,it); return s

# Chart data: {num: (shen, xing, men, tian, di, extra)}
YN5={4:('太阴','天辅','杜门','癸','己',''),9:('螣蛇','天英','景门','己','癸',''),2:('值符','天芮禽','死门','辛','辛',''),3:('六合','天冲','伤门','壬','丁',''),5:('','天禽','','戊','戊',''),7:('九天','天柱','惊门','庚','庚',''),8:('九地','天任','生门','丁','壬',''),1:('玄武','天蓬','休门','丙','乙',''),6:('白虎','天心','开门','乙','丙','')}
Y7={4:('太阴','天英','景门','庚','丁','马'),9:('六合','天芮禽','死门','壬','癸',''),2:('白虎','天柱','惊门','戊','己',''),3:('螣蛇','天辅','杜门','丁','庚',''),5:('','天禽','','癸','癸',''),7:('玄武','天心','开门','乙','戊',''),8:('值符','天冲','伤门','己','壬','○'),1:('九天','天任','生门','辛','乙',''),6:('九地','天蓬','休门','丙','辛','')}
Y9={4:('值符','天任','杜门','己','癸','马'),9:('九天','天冲','景门','丁','戊',''),2:('九地','天辅','死门','癸','丙',''),3:('螣蛇','天蓬','伤门','乙','丁',''),5:('','天禽','','壬','壬',''),7:('玄武','天英','惊门','戊','庚',''),8:('太阴','天心','生门','辛','己',''),1:('六合','天柱','休门','庚','乙',''),6:('白虎','天芮禽','开门','丙','辛','')}
Y8={4:('太阴','天芮禽','死门','辛','癸',''),9:('六合','天柱','惊门','乙','己',''),2:('白虎','天心','开门','丙','辛',''),3:('螣蛇','天英','景门','己','壬',''),5:('','天禽','','丁','丁',''),7:('玄武','天蓬','休门','庚','乙',''),8:('值符','天辅','杜门','癸','戊',''),1:('九天','天冲','伤门','壬','庚',''),6:('九地','天任','生门','戊','丙','')}

def dc(s,cl,l=Inches(0.2),t=Inches(0.7),sz=Inches(4.2)):
    po={4:(0,0),9:(0,1),2:(0,2),3:(1,0),5:(1,1),7:(1,2),8:(2,0),1:(2,1),6:(2,2)}
    pn={1:'坎',2:'坤',3:'震',4:'巽',5:'中',6:'乾',7:'兑',8:'艮',9:'离'}
    pd={4:'东南',9:'南',2:'西南',3:'东',5:'',7:'西',8:'东北',1:'北',6:'西北'}
    cw=sz/3; ch=sz/3
    for nu,(r,c) in po.items():
        x=int(l+c*cw); y=int(t+r*ch)
        rx=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x,y,int(cw),int(ch))
        rx.fill.solid(); rx.fill.fore_color.rgb=RGBColor(0xE8,0xE6,0xDC) if nu==5 else IV
        rx.line.color.rgb=IB; rx.line.width=Pt(0.8)
        tb(s,x+2,y+1,int(cw*0.4),int(ch*0.12),pd[nu],5,c=WG)
        tb(s,x+int(cw*0.6),y+1,int(cw*0.38),int(ch*0.12),pn[nu],6,c=IB,b=True,a=PP_ALIGN.RIGHT)
        if nu in cl:
            d=cl[nu]
            if d[0]: tb(s,x+2,y+int(ch*0.14),cw-4,int(ch*0.14),d[0],6,c=RA,a=PP_ALIGN.CENTER)
            tb(s,x,y+int(ch*0.32),cw,int(ch*0.28),d[3],13,c=DT,b=True,a=PP_ALIGN.CENTER)
            tb(s,x+2,y+int(ch*0.7),int(cw*0.4),int(ch*0.12),d[1],5,c=IB)
            tb(s,x+int(cw*0.55),y+int(ch*0.7),int(cw*0.43),int(ch*0.12),d[2],5,c=IL,a=PP_ALIGN.RIGHT)
            tb(s,x+int(cw*0.6),y+int(ch*0.82),int(cw*0.38),int(ch*0.12),d[4],5,c=WG,a=PP_ALIGN.RIGHT)
            if d[5]: tb(s,x+2,y+int(ch*0.55),cw-4,int(ch*0.12),d[5],5,c=OR,a=PP_ALIGN.CENTER)

def cs(t,sub,cl,it):
    s=ns(); bar(s,t,sub); dc(s,cl,Inches(0.15),Inches(0.65),Inches(4.2))
    bd(s,it,Inches(0.65),Inches(4.6),Inches(8.3),8)
    return s

# ===================== SLIDES =====================

# S1: Title
s=ns()
r=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(2),Inches(1),Inches(9.3),Inches(2.8))
r.fill.solid(); r.fill.fore_color.rgb=IB; r.line.fill.background()
tb(s,Inches(2.5),Inches(1.2),Inches(8.3),Inches(1),'成慈高级奇门讲义',32,c=WH,b=True,a=PP_ALIGN.CENTER)
tb(s,Inches(2.5),Inches(2.2),Inches(8.3),Inches(0.5),'集民间之大成 汇百家之精髓',16,c=RGBColor(0xCC,0xCC,0xDD),a=PP_ALIGN.CENTER)
tb(s,Inches(2.5),Inches(2.8),Inches(8.3),Inches(0.4),'成慈老师 2024年奇门遁甲高级研讨班',13,c=RGBColor(0xAA,0xAA,0xBB),a=PP_ALIGN.CENTER)
bd(s,[('茅山派第46代弟子  道教吕祖蓬莱派第19代弟子',0,False,BT,12),('国学智慧传播者  国学研究实战专家  茅山奇门遁甲术实战应用导师',0,False,BT,12),('收徒10余人  98家企业发展顾问  帮助1000多人解答疑惑',0,False,BT,12),('',0,False,BT),('祖传课程：《时家奇门遁甲》《祖传择日择时法》《民间秘术》《查地理镇物法》等',0,False,WG,10)],Inches(4.3),Inches(1),Inches(11),11)
tb(s,Inches(0.3),Inches(7.1),Inches(12),Inches(0.3),'成慈老师 2024年奇门遁甲高级研讨班',7,c=WG)

# S2: TOC
s=ns(); bar(s,'课程纲要','奇门遁甲高级研讨班主要教学内容')
tb(s,Inches(0.5),Inches(0.85),Inches(6),Inches(0.3),'上篇 基础',13,c=IB,b=True)
tb(s,Inches(6.8),Inches(0.85),Inches(6),Inches(0.3),'下篇 应用',13,c=IB,b=True)
t1=('一、奇门演盘方法\n二、占卜应用类（27项）\n三、奇门演局篇\n四、12神将用法（壬遁法）\n五、隐干用法\n六、占卜发用定律\n七、六亲占卜法\n八、过去未来值符定位\n九、流年流月运势\n十、婚姻合婚占卜\n十一、工作占卜秘诀\n十二、财运投资占卜')
t2=('十三、大事分析思路\n十四、三传用法秘诀\n十五、胎产断男女\n十六、奇门择吉\n十七、阳宅风水占卜\n十八、阴宅风水占卜\n十九、灵异怪病占卜\n二十、奇门外应\n廿一、杂占（考试/走失/疾病/盗贼）\n廿二、天地盘格局\n廿三、盘式代表含义\n廿四、符箓四纵五横')
tb(s,Inches(0.6),Inches(1.2),Inches(6),Inches(5),t1,10,c=BT)
tb(s,Inches(6.9),Inches(1.2),Inches(6),Inches(5),t2,10,c=BT)

# ===== 1. 演局基础 =====
ts('演局基础','时家转盘奇门 阴阳遁18局',[
    ('[基本法则]',0,True,IB,12),('冬至后用阳遁，夏至后用阴遁 阴阳各9局共18局',0,False,BT),
    ('阴遁：逆布六仪，顺布三奇  阳遁：顺布六仪，逆布三奇',0,False,BT),
    ('',0,False,BT),('[六仪顺序] 戊己庚辛壬癸',0,True,DT,11),('[三奇顺序] 乙丙丁（古法顺序）',0,True,DT,11),
    ('',0,False,BT),('[奇门四盘]',0,True,IB,11),('先布地盘 然后天盘 再人盘 最后神盘',0,False,BT),
    ('神盘类似于神鬼等物质，不在五行中',0,False,BT)])

ts('演局步骤一','查四柱定阴阳节气',[
    ('[第一步] 查出四柱天干地支',0,True,IB,11),('日干可在万年历直接查出，只有时干需要推算',0,False,BT),
    ('',0,False,BT),('[推时干口诀] 五鼠遁',0,True,DT,11),
    ('甲己日(子时起甲) 乙庚日(子时起丙) 丙辛日(子时起戊)',0,False,BT),
    ('丁壬日(子时起庚) 戊癸日(子时起壬)',0,False,BT),
    ('',0,False,BT),('[第二步] 定阴遁/阳遁',0,True,IB,11),
    ('冬至夏至用阳遁；夏至冬至用阴遁',0,False,BT),('查出当天所属的二十四节气',0,False,BT)])

ts('演局步骤二','日旬首定符头 三元定局',[
    ('[第三步] 通过日的旬首找元数和局数',0,True,IB,11),
    ('日的旬首=日地支顺序数-日天干顺序数（小于2加12）',0,False,BT),
    ('0甲子旬 10甲戌旬 8甲申旬 6甲午旬 4甲辰旬 2甲寅旬',0,False,BT),
    ('',0,False,BT),('[符头对应]',0,True,DT,11),('上元：甲子、甲午',0,False,BT),
    ('中元：甲寅、甲申',0,False,BT),('下元：甲戌、甲辰',0,False,BT),
    ('',0,False,BT),('[注意规则]',0,True,IB,11),
    ('子午用上元 寅申用中元 辰戌用下元',0,False,BT),
    ('日干前5位(甲乙丙丁戊)直接使用；后5位(己庚辛壬癸)往下推一元',0,False,BT)])

ts('二十四节气三元定局','阳遁九局 阴遁九局',[
    ('[阳遁三元定局]',0,True,IB,11),
    ('冬至一七四 小寒二八五 大寒三九六',0,False,BT),
    ('立春八五二 雨水九六三 惊蛰一七四',0,False,BT),
    ('春分三九六 清明四一七 谷雨五二八',0,False,BT),
    ('立夏四一七 小满五二八 芒种六三九',0,False,BT),
    ('',0,False,BT),('[阴遁三元定局]',0,True,IB,11),
    ('夏至九三六 小暑八二五 大暑七一四',0,False,BT),
    ('立秋二五八 处暑一四七 白露九三六',0,False,BT),
    ('秋分七一四 寒露六九三 霜降五八二',0,False,BT),
    ('立冬六九三 小雪五八二 大雪四七一',0,False,BT),
    ('',0,False,BT),('例：小雪582 上元5局、中元8局、下元2局',0,True,IB,10)])

ts('演局步骤三至六','布地盘 找值符值使 天盘演局',[
    ('[第四步] 布地盘三奇六仪',0,True,IB,11),
    ('顺序：戊己庚辛壬癸丁丙乙',0,False,BT),
    ('阴遁逆布九宫 阳遁顺布九宫 从局数对应宫开始布',0,False,BT),
    ('',0,False,BT),('[第五步] 找值符值使',0,True,IB,11),
    ('值符=时辰当班的天星（天盘首领）',0,False,BT),
    ('值使=时辰当班的门将（人盘首领）',0,False,BT),
    ('找出时辰旬首，旬首原宫位星门就是值符值使',0,False,BT),
    ('时辰旬首=时支-时干（同找日旬首方法）',0,False,BT),
    ('',0,False,BT),('[第六步] 天盘演局',0,True,IB,11),
    ('值符加到时干同宫，其余九星依次顺转',0,False,BT),
    ('天盘永远顺转，不管阴阳遁',0,False,BT),
    ('天盘顺序：蓬任冲辅英芮禽柱心',0,False,BT)])

ts('人盘与神盘演局','值使加时辰宫 八神顺逆',[
    ('[第七步] 人盘演局',0,True,IB,11),
    ('值使为首领，跟着时辰宫转',0,False,BT),
    ('时辰宫=旬首隔宫数（时干数-1）',0,False,BT),
    ('八门顺序：休生伤杜景死惊开',0,False,BT),
    ('阳顺阴逆推时辰宫',0,False,BT),
    ('',0,False,BT),('[第八步] 神盘演局',0,True,IB,11),
    ('神盘顺序：值符、螣蛇、太阴、六合、白虎、玄武、九地、九天',0,False,BT),
    ('值符加到天盘星值符上 阳遁顺转阴遁逆转',0,False,BT),
    ('',0,False,BT),('[第九步] 旬空',0,True,IB,11),
    ('以时旬空为主，日旬空为辅助',0,False,BT),
    ('旬空=时候未到无力之象 空亡宫为虚宫对宫为孤宫',0,False,BT),
    ('甲子旬戌亥空  甲戌旬酉申空  甲申旬午未空',0,False,BT),
    ('甲午旬辰巳空  甲辰旬寅卯空  甲寅旬子丑空',0,False,BT)])

ts('第十步 人盘隐干排局','代表隐藏事物和状态',[
    ('[人盘隐干]',0,True,IB,11),
    ('可以不用写在奇门局上，自己在心里即可',0,False,BT),
    ('例：开门在2宫，6宫地盘奇仪为乙，开门原宫位6宫→隐干乙',0,False,BT),
    ('其他类推，代表隐藏事物和状态',0,False,BT),
    ('',0,False,BT),('甲午旬辰巳空  甲辰旬寅卯空  甲寅旬子丑空',0,False,BT)])

# ===== 实例 =====
cs('实例：阴遁5局庚午时','2010.11.25 12:06 庚寅年丁亥月己卯日庚午时',YN5,[
    ('[本例完整步骤]',0,True,IB,9),('',0,False,BT),
    ('1 日干己 甲己日子时起甲 推到午时庚午',0,False,BT),
    ('2 小雪节气 阴遁',0,False,BT),
    ('3 日支4-日干6=-2+12=10 甲戌旬 辰戌下元 日后5推上元 小雪上元5局',0,False,BT),
    ('4 布地盘：5宫起戊逆布 543219876',0,False,BT),
    ('5 时干庚 时支7-时干7=0甲子旬 戊落中5 天禽值符 死门值使',0,False,BT),
    ('6 值符天禽加时干庚 值使死门隔6宫落8宫',0,False,BT),
    ('',0,False,BT),('[旬空] 时戌亥空(6宫) 日酉申空(7、2宫)',0,True,RA,9),
    ('',0,False,BT),('[三传] 初传7宫(开始)->中传1宫(过程)->末传2宫(结束)',0,True,IB,9),
    ('[过去值符] 甲午辛落8宫 天任星落4宫=过去趋势',0,False,BT),
    ('[将来值符] 甲寅癸落6宫 天心星落8宫=将来趋势',0,False,BT)])

cs('实例：阳7局己未时','2009.12.24 14:51 五不遇时',Y7,[
    ('[此局特点] 五不遇时（时干克日干）',0,True,RA,9),
    ('干支：己丑年丙子月癸卯日己未时',0,False,BT),
    ('值符：天冲  值使：伤门  旬首：甲寅癸',0,False,BT),
    ('',0,False,BT),('此例用于隐干用法讲解：',0,True,IB,9),
    ('天盘隐干：6宫天蓬星原宫1宫地盘干辛 隐干辛',0,False,BT),
    ('人盘隐干：6宫休门原宫1宫地盘干辛 隐干辛',0,False,BT),
    ('暗干排法：时干加值使门阳顺阴逆',0,False,BT),
    ('应期干入中：时干己加中宫',0,False,BT),
    ('',0,False,BT),('应期：庚落6宫 对应庚时庚年庚月',0,True,IB,9)])

# ===== 12神将 =====
ts('12神将总论','壬遁结合法 定将活将 吉凶含义',[
    ('[神将两种]',0,True,IB,12),
    ('定将：9宫中12地支固定不动（如1宫定将子将）',0,False,BT),
    ('活将：月将加到时辰宫活布',0,False,BT),
    ('',0,False,BT),('[布将方法]',0,True,IB,11),
    ('找出当月月将，加到时辰宫(值使宫)上',0,False,BT),
    ('阳遁顺布九宫，阴遁逆布九宫',0,False,BT),
    ('12神将只用9个，其余3个隐藏',0,False,BT),
    ('',0,False,BT),('[12神将总览]',0,True,IB,11),
    ('子贵神(1)吉 贵人官员钱财  丑天厄(2)凶 暗疾阻碍破财',0,False,BT),
    ('寅权衡(3)吉 权威权力公检法  卯破损(4)凶 破财开支',0,False,BT),
    ('辰奸私(5)半凶 自私奸诈阴谋  巳文曲(6)吉 聪明好学文书',0,False,BT),
    ('午天福(7)吉 官方文书酒席  未驿马(8)次吉 变动出行',0,False,BT),
    ('申劳孤(9)半凶 忙碌劳苦  酉性躁(10)凶 口舌官司',0,False,BT),
    ('戌技巧(11)吉 技术艺术  亥长寿(12)次吉 拖拉缓慢',0,False,BT)])

# 12神将详细：各1-2个
for n,(nm,desc,cl) in enumerate([
    ('子神后(水)','隐私暗昧妇女之事。肾膀胱痢疾血病。临太阴隐私，临六合暗自相合，临丙丁男女主动',RA),
    ('丑大吉(土)','田宅园圃斗争。脾肺小肠。凡事有碍有堵隔',BT),
    ('寅功曹(木)','水器文书婚姻财锦官禄。胆筋脉发口眼三焦。主有权力来势猛',BT),
    ('卯太冲(木)','万物离散破坏。左肋足肝。破损门面事。临戊生门钱财损',BT),
    ('辰天罡(土)','头讼死丧田宅旧事。胃肩胸。暗藏困惑狡诈陈旧',BT),
    ('巳太乙(火)','怪异口舌斗争文书神。心胞络三焦咽喉。事急主怪异',BT),
    ('午胜光(火)','文书官事光亮火热。血光心虚头小肠。与他人有关变化分支',BT),
    ('未小吉(土)','变动酒食婚姻喜事马星。肝脱脊。事马上有变喜事',BT),
    ('申传送(金)','奔波道路疾病信耗。肺胆大肠骸骨。流动性费力。申见庚白虎',BT),
    ('酉从魁(金)','急躁生气阴私解散。皮毛口耳目精血。易生气口舌柔弱',BT),
    ('戌河魁(土)','技术技巧心灵手巧。命门膀胱足脚。困惑诈欺旧事重来',BT),
    ('亥登明(水)','初等于天照万国天门。肝肾发头。拖拉不干脆。占寿长寿',BT),
]):
    ts(f'12神将详解：{nm}','病情 环境 事情状态 神将类象',[
        (f'[{nm}]',0,True,cl,10),(f'{desc}',0,False,BT),
        ('',0,False,BT),('[人物类象]',0,True,IB,10)]+
        [('  '+s,0,False,BT) for s in {
            '子':'少男 公门人 军警 盗贼 黑衣人','丑':'老妇 贵人 尊长 神佛 死尸',
            '寅':'老男 政府工作 丈夫 贵人','卯':'手工业者 兄弟 妇女 盗贼',
            '辰':'男人 医生 僧道 腰脚痛','巳':'少女 少妇 乞丐',
            '午':'少女 女秘书 血光之人','未':'老妇 巫师 寡妇 尼姑',
            '申':'男人 军人 公安 行人 恶人','酉':'女人 女贵人 卖酒之人',
            '戌':'男人 农民 清洁工 信佛道','亥':'少女 小孩 犯人 盗贼'
        }[['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'][n]].split('  ')]
    )

# 手上推法
ts('手上12神将推法','日行宫为求测人 时行宫为求测事',[
    ('[掌诀推法] 庚寅年十月初五午时占求财',0,True,IB,11),
    ('',0,False,BT),('第一步：从寅位起年（庚寅年）',0,False,BT),
    ('第二步：从寅起月顺转至十月（亥）',0,False,BT),
    ('第三步：从亥起初一顺至初五（卯）',0,False,BT),
    (' 卯位为求测人，卯主堵，时运不佳',0,False,BT),
    ('第四步：从卯起子时顺至午时（酉）',0,False,BT),
    (' 酉位为求测事，酉主生气不愉快',0,False,BT),
    ('',0,False,BT),('[结论] 逢冲事有变，相克不成',0,True,RA,11),
    ('',0,False,BT),('用法口诀：',0,True,IB,10),
    ('子为子息渔屠儿 丑为贤者又僧尼',0,False,BT),
    ('寅婿道士官吏 卯术沙门长子空',0,False,BT),
    ('辰为魁卒凶顽恶 巳朋长女为窑皂',0,False,BT),
    ('妇人宫女蚕姑午 姑姨舅妹小吉未',0,False,BT),
    ('申猎医巫银铁匠 少女婢妇姐从魁酉',0,False,BT),
    ('卒奴吏官仆凶戌 幼子寇盗亥宫推',0,False,BT)])

# ===== 隐干 =====
ts('奇门隐干用法(一)','天盘隐干 人盘隐干',[
    ('[第一种：天盘隐干]',0,True,IB,11),
    ('天盘星所带原来宫位地盘干（天盘活干）',0,False,BT),
    ('例：6宫天蓬星原宫1宫地盘干辛 隐干为辛',0,False,BT),
    ('',0,False,BT),('天盘隐干好比遗传基因',0,True,DT),
    ('例：6宫天盘隐干辛好比1宫的儿子',0,False,BT),
    ('天盘隐干=现在和显露事情',0,False,BT),
    ('隐干原来宫位=过去和隐藏事情',0,False,BT),
    ('',0,False,BT),('[第二种：人盘隐干]',0,True,IB,11),
    ('人盘(八门)原来宫位地盘奇仪',0,False,BT),
    ('同宫内天盘星和八门好比一母所生，遗传基因相同',0,False,BT),
    ('主人盘隐藏事情和暗藏状态',0,False,BT),
    ('例：占婚姻 休门隐干辛 家庭有问题',0,False,BT)])

ts('奇门隐干用法(二)','暗干 应期干入中法',[
    ('[第三种：暗干]',0,True,IB,11),
    ('排法：时干加到值使门阳顺阴逆',0,False,BT),
    ('暗干、天盘活干、地盘干形成三角交叉点',0,False,BT),
    ('显示事物信息和求测者心里的另一个人',0,False,BT),
    ('注：这方法用不好有些乱，教学中不常用',0,False,BT),
    ('',0,False,BT),('[第四种：应期干入中法]',0,True,IB,11),
    ('时干加到中宫阳顺阴逆',0,False,BT),
    ('显示宇宙在时间上的分量',0,False,BT),
    ('',0,False,BT),('用法：判断时间应期',0,True,DT,10),
    ('例：时干己加中宫 庚落6宫 应期庚时庚年庚月',0,False,BT),
    ('若地盘干和应期干相同更准确 要结合三传及旬空',0,False,BT)])

# More slides will be added in the next chunk...
print(f'Build part 1: {len(prs.slides)} slides')
# Save partial first
prs.save('e:\\wenan catch\\test_part2.pptx')
print('Saved test_part2.pptx')
