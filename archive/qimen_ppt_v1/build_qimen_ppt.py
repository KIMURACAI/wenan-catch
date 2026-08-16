#!/usr/bin/env python3
"""Build Qimen Dunjia lecture PPT with standard 九宫排盘图."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# Colors
INK_BLUE = RGBColor(0x1B, 0x36, 0x5D)
INK_LIGHT = RGBColor(0x2D, 0x5A, 0x8A)
PARCHMENT = RGBColor(0xF5, 0xF4, 0xED)
DARK_TEXT = RGBColor(0x1A, 0x1A, 0x18)
BODY_TEXT = RGBColor(0x33, 0x33, 0x30)
RED_ACCENT = RGBColor(0x8B, 0x00, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
WARM_GRAY = RGBColor(0x5A, 0x5A, 0x55)
LIGHT_BG = RGBColor(0xFA, 0xF9, 0xF5)

OUT_DIR = r"e:\wenan catch"

def add_bg(slide, color=PARCHMENT):
    """Set slide background."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_title_bar(slide, text, left=Inches(0.5), top=Inches(0.3), width=Inches(9)):
    """Add a styled title bar."""
    # Title bar background
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), top - Inches(0.05), Inches(10), Inches(0.55)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = INK_BLUE
    bar.line.fill.background()

    # Title text
    txBox = slide.shapes.add_textbox(left, top, width, Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = WHITE
    return txBox

def add_subtitle(slide, text, top=Inches(1.0)):
    """Add subtitle text."""
    txBox = slide.shapes.add_textbox(Inches(0.5), top, Inches(9), Inches(0.4))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(14)
    p.font.color.rgb = INK_LIGHT
    p.font.italic = True

def add_body_text(slide, text, top=Inches(1.5), left=Inches(0.7), width=Inches(8.5), font_size=13):
    """Add body text with bullet points."""
    txBox = slide.shapes.add_textbox(left, top, width, Inches(4.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    lines = text.strip().split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line.strip()
        p.font.size = Pt(font_size)
        p.font.color.rgb = BODY_TEXT
        p.space_after = Pt(4)
        p.space_before = Pt(2)
        if line.startswith("【") or line.startswith("一") or line.startswith("二") or line.startswith("三"):
            p.font.bold = True
            p.font.size = Pt(font_size + 1)
            p.font.color.rgb = INK_BLUE
        if line.startswith("●"):
            p.level = 1
            p.font.size = Pt(font_size - 1)
    return txBox

def add_chart_image(slide, chart_name, left=Inches(0.5), top=Inches(1.5), width=Inches(4.5)):
    """Embed a chart SVG as image (converted by python-pptx internally)."""
    path = os.path.join(OUT_DIR, chart_name)
    if os.path.exists(path):
        # python-pptx doesn't support SVG directly, but we can convert to PNG
        # For SVG, we'll use a placeholder rectangle and add text
        pass
    return None

def add_text_block(slide, text, left, top, width, height, font_size=11, bold=False, color=BODY_TEXT, align=PP_ALIGN.LEFT):
    """Add a text block at specific position."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = align
    return txBox

def add_rounded_box(slide, left, top, width, height, fill_color=LIGHT_BG, line_color=INK_BLUE):
    """Add a rounded rectangle."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = line_color
    shape.line.width = Pt(1)
    return shape

def add_footer(slide, text="成慈老师高级奇门研讨班教材"):
    """Add footer text."""
    txBox = slide.shapes.add_textbox(Inches(0.3), Inches(7.0), Inches(9), Inches(0.3))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(8)
    p.font.color.rgb = WARM_GRAY
    p.alignment = PP_ALIGN.LEFT

def make_title_slide(prs):
    """Slide 1: Title."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    add_bg(slide)

    # Big title area
    add_rounded_box(slide, Inches(0.5), Inches(0.8), Inches(9), Inches(2.8), fill_color=INK_BLUE, line_color=INK_BLUE)
    add_text_block(slide, "成慈高级奇门讲义", Inches(1), Inches(1.0), Inches(8), Inches(1.2),
                   font_size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text_block(slide, "集民间之大成 · 汇百家之精髓", Inches(1), Inches(2.2), Inches(8), Inches(0.5),
                   font_size=18, color=RGBColor(0xCC, 0xCC, 0xCC), align=PP_ALIGN.CENTER)
    add_text_block(slide, "成慈老师 2024年奇门遁甲高级研讨班", Inches(1), Inches(2.7), Inches(8), Inches(0.5),
                   font_size=14, color=RGBColor(0xAA, 0xAA, 0xAA), align=PP_ALIGN.CENTER)

    # Author info
    add_rounded_box(slide, Inches(2), Inches(4.0), Inches(6), Inches(2.5), fill_color=LIGHT_BG)
    info_items = [
        "茅山派第46代弟子 · 道教吕祖蓬莱派第19代弟子",
        "国学智慧传播者 · 国学研究实战专家",
        "茅山奇门遁甲术实战应用导师",
        "两年前后收徒20余人 · 被聘为98家企业发展顾问",
        "帮助1000多人答疑解惑以及策划布局"
    ]
    for i, item in enumerate(info_items):
        add_text_block(slide, f"▸ {item}", Inches(2.3), Inches(4.2 + i * 0.45), Inches(5.5), Inches(0.4),
                       font_size=12, color=BODY_TEXT)

def make_toc_slide(prs):
    """Slide 2: Table of Contents."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_title_bar(slide, "课程纲要")
    add_subtitle(slide, "奇门遁甲高级研讨班  ·  主要教学内容")

    left_col = [
        "一、奇门演盘方法（数字加减法）",
        "二、占卜应用类（27项秘诀）",
        "三、奇门演局篇（起局定局）",
        "四、12神将用法（壬遁法）",
        "五、隐干用法（四种隐干）",
        "六、占卜发用定律（年命/日干/时干/用神）",
        "七、六亲占卜法",
        "八、流年流月运势",
    ]
    right_col = [
        "九、婚姻合婚占卜",
        "十、工作占卜秘诀",
        "十一、财运与投资占卜",
        "十二、三传用法（壬遁结合）",
        "十三、胎产断男女",
        "十四、阳宅风水占卜",
        "十五、阴宅风水占卜",
        "十六、择吉与奇门外应",
    ]
    for i, item in enumerate(left_col):
        add_text_block(slide, item, Inches(0.7), Inches(1.5 + i * 0.55), Inches(4), Inches(0.5),
                       font_size=12, color=BODY_TEXT)
    for i, item in enumerate(right_col):
        add_text_block(slide, item, Inches(5.2), Inches(1.5 + i * 0.55), Inches(4.5), Inches(0.5),
                       font_size=12, color=BODY_TEXT)
    add_footer(slide)

def make_slide_with_chart(prs, title, subtitle, body_text, chart_file, chart_left=Inches(0.3), chart_top=Inches(1.4)):
    """Create a slide with text on the right and Qimen chart on the left."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_title_bar(slide, title)
    add_subtitle(slide, subtitle)

    # Chart on the left side
    chart_path = os.path.join(OUT_DIR, chart_file)
    if os.path.exists(chart_path):
        # python-pptx doesn't do SVG natively, use placeholder
        rect = add_rounded_box(slide, chart_left, chart_top, Inches(4.2), Inches(4.2),
                                fill_color=LIGHT_BG, line_color=INK_BLUE)
        add_text_block(slide, f"[奇门排盘图]\n{chart_file.replace('.svg','').replace('qimen_','')}",
                       chart_left + Inches(0.3), chart_top + Inches(1.5), Inches(3.6), Inches(1.2),
                       font_size=11, color=INK_LIGHT, align=PP_ALIGN.CENTER)

    # Text on the right
    add_body_text(slide, body_text, top=Inches(1.5), left=Inches(4.8), width=Inches(4.8), font_size=11)
    add_footer(slide)
    return slide

def make_text_slide(prs, title, subtitle, body_text):
    """Create a text-only slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_title_bar(slide, title)
    add_subtitle(slide, subtitle)
    add_body_text(slide, body_text, top=Inches(1.5))
    add_footer(slide)
    return slide


# ========== BUILD ==========

def build():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slides content
    slides_data = [
        ("title", None, None),  # special

        ("toc", None, None),  # special

        # == 奇门演局篇 ==
        ("text", "奇门演局·起局方法", "时家转盘奇门遁甲  ·  阴阳遁18局",
         """【阴阳遁法则】
● 冬至后用阳遁，夏至后用阴遁
● 阴阳各9局，共18局
● 阴遁：逆布六仪，顺布三奇
● 阳遁：顺布六仪，逆布三奇

【六仪】戊、己、庚、辛、壬、癸
【三奇】乙、丙、丁（古法顺序）

【四盘顺序】
先布地盘 → 再布天盘 → 再布人盘 → 最后神盘

【定局步骤】
一、查四柱天干地支
二、定阴阳遁（节气）
三、找元数（日旬首定符头）
四、布地盘三奇六仪
五、找值符值使
六～八、天盘·人盘·神盘演局"""),

        # 阴遁5局实例
        ("chart", "阴遁5局实例·庚午时", "2010年11月25日12:06  |  庚寅年 丁亥月 己卯日 庚午时",
         """【本例步骤】
一、日干己 → 甲己日甲子起 → 推得庚午时
二、小雪节气 → 阴遁
三、日旬首甲戌 → 辰戌下元，日后五推上元
    小雪"582" → 上元5 → 阴遁5局
四、值符：天禽星（落中5宫）
    值使：死门（落8宫）
五、天盘天禽加时干庚

【重要概念】
● 值符 = 天盘首领（当班天星）
● 值使 = 人盘首领（当班门将）
● 旬空：戌亥（时空）/ 酉申（日空）
● 三传：初→地盘值符宫 / 中→天盘值符 / 末→值使宫""",
         "qimen_阴遁5局_庚午时.svg"),

        # 12神将
        ("text", "12神将用法（壬遁法）", "神将吉凶含义·具体用法·掐指辨吉凶",
         """【神将总论】
子贵神（吉）·丑天厄（凶）·寅权衡（吉）·卯破损（凶）
辰奸私（半凶）·巳文曲（吉）·午天福（吉）·未驿马（次吉）
申劳孤（半凶）·酉性躁（凶）·戌技巧（吉）·亥长寿（次吉）

【布将方法】
● 月将加值使门（时辰宫）
● 阳遁顺布九宫，阴遁逆布九宫
● 12神将只用9个，其余3个隐藏

【两种神将】
● 定将：9宫中12地支固定不动（如1宫子将）
● 活将：月将加时辰宫活布

【掌诀推法】
日行宫=求测人，时行宫=求测事
年月日时四步推演，逢冲主变，相克不成"""),

        # 隐干用法
        ("text", "奇门隐干用法", "四种隐干排法原理及应用",
         """【四种隐干】
一、天盘隐干 → 天盘星原宫地盘干（遗传基因）
    主现在、显露之事；原宫主过去、隐藏

二、人盘隐干 → 八门原宫地盘干
    主人盘隐藏状态（如休门辛=家庭有问题）

三、暗干 → 时干加值使门阳顺阴逆
    三角交叉点显示隐藏信息

四、应期干入中 → 时干加中宫阳顺阴逆
    判断时间应期（庚落6宫=庚时/庚年/庚月）

【用法要点】
● 天盘为客，地盘为主
● 隐干如遗传基因，需参照原宫位"""),

        # 占卜定律
        ("text", "占卜发用·个人状态定律", "年命宫·日干宫·时干宫·用神宫",
         """【年命宫定律】
年命+坐宫+日干+时干+日支 同宫 → 自身宫
年命信息大于日干一半

【日干宫定律】
日干代表求测者目前状态，非运势自身宫
需与年命/日支/方位/用神重合才准确

【时干宫定律】
时干≠事情结果，只为求测人目前事情状态
时干+用神同宫 → 才代表求测之事

【明宫·暗宫】
年命宫（自身宫）= 明宫
对宫 = 暗宫（隐藏内心之事）
明暗双宫是断事核心"""),

        # 六亲
        ("text", "六亲占卜秘诀", "不用找用神，只靠六亲断事",
         """【男命六亲】
● 妻  子：他克不同性（壬→丁）
● 第三者：他克同性（壬→丙）
● 父  亲：生他同性（壬→庚）
● 母  亲：生他不同性（壬→辛）
● 儿  子：他生同性（壬→戊）
● 女  儿：他生不同性（壬→己）
● 官  位：克他不同性
● 小  人：克他同性

【女命六亲】（相反）
夫=克她不同性，三=克她同性
母=生她同性，父=生她不同性
官=她克不同性，小人=她克同性

【关键】
夫妻同宫感情不好，对宫相冲感情变动"""),

        # 流年运势
        ("text", "流年流月运势秘诀", "年命·太岁·月干生克关系",
         """【流年吉凶判断】
● 年命克太岁 = 有灾（伤灾、破财）
  注意投资和出行安全
● 太岁克年命 = 有灾（较轻）
  太岁不可动，破财病灾
● 太岁生年命 = 大吉（大胆去做）
● 年命生太岁 = 付出大、开支大
● 年命与太岁相同 = 平平

【太岁宫细节】
太岁宫的门星信息 = 具体事物
例：太岁宫有白虎伤门
→ 注意车辆道路安全

【流月】月干落宫克年命宫 = 该月不顺"""),

        # 婚姻合婚
        ("text", "婚姻合婚占卜秘诀", "合婚·婚姻纠纷·感情状态判断",
         """【合婚方法】
● 看男女年命宫生克
● 相生不落空 = 结果好
● 相克 = 败局不合适
● 伏吟：晚婚 / 反吟：早婚多乱

【感情状态】
● 乙奇女方、庚为男方
● 乙庚相克/同宫 = 感情不好
● 乙下临辛 = 女方要走
● 庚下临丁 = 男方有第三者

【家庭状态】
● 休门 = 家庭整体气氛
● 六合 = 婚姻整体状态
● 六合落空/临死门 = 感情破裂

【二婚标志】伏吟局、反吟局"""),

        # 工作占卜
        ("text", "工作占卜秘诀", "升职·调换工作·工作内部问题",
         """【用神】开门 = 工作整体状态
● 开门被制 = 有压力不顺心
● 开门门迫 = 不稳定易调换
● 开门落空 = 迷茫无力
● 开门入墓(8宫) = 没发展活力

【六亲官位】
男：克他不同性=官，同性=小人
女：她克不同性=官，同性=小人
工作贵人=官宫，小人=鬼位

【用神分类】
公务员→休门 / 技术→杜门
店铺→开门 / 教育→天辅星
房地产→生门 / 交通→伤门

【主客时机】
天盘克地盘=利客（宜动）
地盘生天盘=利客（宜动）
反之=利主（不动）"""),

        # 财运
        ("text", "财运与投资占卜秘诀", "财运判断·投资时机·商业决策",
         """【财运判断】
一、看年命宫（运势根基）
二、看甲子戊落宫（财产整体）
   戊击刑/戊加辛=破财
   戊临壬=钱财困
   戊癸合=财上有合作
三、看生门落宫（利润）
   生门被制=不得力
   生门门迫=有变
四、看六亲财位
   男：他克同性=财位
   女：克她同性=财位

【投资决策七步】
1. 戊（固有资金）→ 天盘落宫
2. 生门（利润）→ 落宫吉凶
3. 年命（运气）→ 好坏
4. 六合+合作方年命
5. 生门与戊的关系
6. 三传 → 发展过程
7. 主客 → 时机"""),

        # 三传
        ("text", "三传用法秘诀（壬遁结合法）", "初传·中传·末传 事物发展三部曲",
         """【三传结构】
初传 → 地盘值符宫（开始）
中传 → 天盘值符宫（过程）
末传 → 值使门落宫（结束）

【三传落宫分析】
● 三传同宫 = 伏吟，拖沓，需抓源头
● 初中同宫 = 开始与中间密不可分
● 初末同宫 = 首尾呼应，重视开始
● 中末同宫 = 关键在中间阶段

【三传落空】
● 初传落空 = 开始没做好
● 中传落空 = 中间有虚
● 末传落空 = 收尾没收好

【策划应用】
● 天盘克地盘 = 利客，主动去做
● 地盘克天盘 = 利主，谨慎行事"""),

        # 胎产
        ("text", "胎产断男女秘诀", "主客法·直接占测与间接占测的区别",
         """【关键区分】
直接占测（孕妇自己问）→ 直接看坤宫
间接占测（亲属代问）→ 用六亲找对应宫

【判断步骤】
1. 坤宫天盘星阴阳
  阳星：蓬、任、冲、辅
  阴星：英、芮、柱、心
2. 星与所带天干阴阳相同 → 直接定
  阳星阳干=男 / 阴星阴干=女
3. 星与干阴阳不同 → 改看八门阴阳

【胎的判断】
年命/日干入局处于十天干"胎"状态
= 此人已怀孕"""),

        # 阳宅
        ("chart", "阳宅风水占卜", "不到场全知道·奇门入地看风水",
         """【十个判断维度】
一、生门宫 → 整体地理环境
二、坐向（坎离宫）→ 九星旺衰
三、值使门 → 大门口吉凶
四、值符宫 → 坐山来龙人丁
五、乙奇落宫 → 左青龙砂
六、辛落宫 → 右白虎砂
七、壬落宫 → 来水财运
八、癸落宫 → 厕所去水
九、丙落宫 → 灶厨房
十、丁落宫 → 香火神位

【要诀】一流先生看星斗
风水看长远，九星旺衰为主""",
         "qimen_阳7局_己未时.svg"),

        # 阴宅
        ("chart", "阴宅风水占卜", "坟地吉凶·先人保佑·来龙地脉",
         """【九个判断维度】
一、死门宫 → 整个坟地情况
二、死门天地盘 → 先人是否保佑后代
三、值使门 → 明堂宽阔
四、白虎宫 → 墓碑情况
五、值符宫 → 来龙吉凶
六、乙奇宫 → 青龙砂（后代男性）
七、辛宫   → 白虎砂（后代女性）
八、壬宫   → 来水财运
九、地盘值符 → 坟墓地脉

【关键】
● 地盘生天盘 = 先人保佑后代
● 死门落空 = 无龙气
● 龙抱虎出知府 / 虎抱龙万事凶""",
         "qimen_阳8局_戊午时.svg"),

        # 择吉
        ("text", "奇门择吉·看日子时辰方位", "时空合一·吉格选择法",
         """【择吉步骤】
一、起念起局（时空合一）
二、找吉格（无击刑、入墓、门迫）
三、选宫：开门（开业）/ 生门（盖房）/ 值符宫

【天地盘格局·吉格选要】
天遁（丙+生门+丁）→ 百事俱吉
地遁（乙+开门+己）→ 造屋埋葬吉
人遁（太阴+丁+休门）→ 万事吉利
龙回首（甲值符+丙）→ 百事吉
鸟跌穴（丙+甲值符）→ 百战百胜
三诈五假 → 出兵嫁娶皆吉

【选日干方法】
宝日（日干生日支）大吉
义日（日支生日干）次吉
和日（日干日支比和）次吉
制日（日干克日支）平日
伐日（日支克日干）凶"""),

        # 外应
        ("text", "奇门外应看法秘诀", "直接判断·间接判断·118种外应",
         """【两种判断角度】
直接判断：
● 外应本身即结论
● 例：有人占测婚姻忽来一人 → 有插足者
● 例：占测升职路上上坡 → 上升之象

间接判断：
● 外应特征进入奇门局分析
● 例：穿黑衣（1宫）/ 到东方（3宫）
● 黄衣女（看9宫好坏）

【常见外应】
● 云开见日 → 事必争辉
● 震雷 → 虚惊
● 水流 → 亨通顺利
● 坚石 → 坚定信念成功
● 松柏 → 健康长寿
● 乌鸦 → 灾将至 / 喜鹊 → 喜将至
  （共118种外应，详见讲义原文）"""),

        # 杂占
        ("text", "杂占用法秘诀", "考试·走失·疾病·凶杀·盗贼",
         """【考试占测】
学生→天芮星 / 考试部门→天辅星 / 试卷→丁奇
天芮克天辅/天辅生天芮 = 能考上

【行人走失】
年命宫好坏 = 平安状态
六合 = 方位方向
伏吟=内地 / 反吟=外地

【疾病占测】
年命+天芮星 = 病因
年命十二状态 = 疾病程度
三传 = 病情发展

【凶杀案】
死门=死人 / 庚=杀人犯
庚所在方位 = 凶手位置

【盗贼】
玄武=小偷 / 天蓬星=大盗
白虎=警察 / 杜门=公安部门"""),

        # 符箓
        ("text", "民间奇门法术·四纵五横符箓", "地理避凶法·开工动土用法",
         """【四纵五横避凶法】
用途：动土开工、避煞

使用方法：
1. 黄纸朱砂书符，念咒语
2. 贴于动工处
3. 触犯煞神时：剑指或三尖香
   空书此符并念咒：
   "天无忌，地无忌，阴阳无忌，百无禁忌"

注意：不可对着神像书画"""),
    ]

    # Build slides
    for item in slides_data:
        slide_type = item[0]
        if slide_type == "title":
            make_title_slide(prs)
        elif slide_type == "toc":
            make_toc_slide(prs)
        elif slide_type == "text":
            title, subtitle, body = item[1], item[2], item[3]
            make_text_slide(prs, title, subtitle, body)
        elif slide_type == "chart":
            title, subtitle, body, chart_file = item[1], item[2], item[3], item[4]
            make_slide_with_chart(prs, title, subtitle, body, chart_file)

    # Save
    output_path = os.path.join(OUT_DIR, "成慈高级奇门讲义.pptx")
    prs.save(output_path)
    print(f"PPT saved: {output_path}")
    print(f"Total slides: {len(prs.slides)}")


if __name__ == "__main__":
    build()
