#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Part2: runs build_dense_ppt.py then adds more slides."""
import sys; sys.path.insert(0, '.')
# Run part1
import build_dense_ppt as p1
# p1.prs now has ~2 slides, add ~33 more
prs = p1.prs
IB=p1.IB; IL=p1.IL; PC=p1.PC; IV=p1.IV; BT=p1.BT; RA=p1.RA; WH=p1.WH; WG=p1.WG; OR=p1.OR; B2=p1.B2; BD=p1.BD
C=p1.C; Inches=p1.Inches; Pt=p1.Pt; PP_ALIGN=p1.PP_ALIGN; MSO_SHAPE=p1.MSO_SHAPE; RGBColor=p1.RGBColor
ns=p1.ns; tx=p1.tx; bg=p1.bg; rn=p1.rn; gc=p1.gc; B=p1.B; SW=p1.SW
YN5=p1.YN5; Y9=p1.Y9; Y8=p1.Y8

def hdr(s,t):
    tx(s,B,Inches(0.58),Inches(12.53),Inches(0.2),t,10,c=C(IB),b=True)

# ===== ADD SLIDES =====
# S3: 演局
s=ns(); bg(s,'奇门演局基础','时家转盘奇门 阴阳遁18局 四盘构成')
rn(s,B,Inches(0.7),Inches(7.2),Inches(5.5))
tx(s,B+Inches(0.1),Inches(0.75),Inches(7),Inches(0.2),'【基本法则】',10,c=C(IB),b=True)
tx(s,B+Inches(0.1),Inches(1.0),Inches(7),Inches(4.5),
   '冬至后阳遁 夏至后阴遁 阴阳各9局共18局\n阴遁逆布六仪顺布三奇 阳遁顺布六仪逆布三奇\n六仪:戊己庚辛壬癸 三奇:乙丙丁\n\n奇门四盘:先布地盘->天盘->人盘->神盘\n神盘类似神鬼等物质,不在五行中\n\n推时干口诀(五鼠遁):\n甲己日起甲子 乙庚日起丙子\n丙辛日起戊子 丁壬日起庚子 戊癸日起壬子\n\n定局步骤:\n1.查四柱(万年历) 2.定阴阳(节气)\n3.找元数(日旬首定符头)\n4.布地盘三奇六仪\n5.找值符值使 6-8.天盘人盘神盘\n9.旬空 10.人盘隐干',9,c=C(BT))
rn(s,Inches(7.7),Inches(0.7),Inches(5.3),Inches(5.5),C(B2))
tx(s,Inches(7.8),Inches(0.75),Inches(5.1),Inches(0.2),'三元定局歌诀',10,c=C(IB),b=True)
tx(s,Inches(7.8),Inches(1.0),Inches(5.1),Inches(5),
   '阳遁:\n冬至一七四 小寒二八五 大寒三九六\n立春八五二 雨水九六三 惊蛰一七四\n春分三九六 清明四一七 谷雨五二八\n立夏四一七 小满五二八 芒种六三九\n\n阴遁:\n夏至九三六 小暑八二五 大暑七一四\n立秋二五八 处暑一四七 白露九三六\n秋分七一四 寒露六九三 霜降五八二\n立冬六九三 小雪五八二 大雪四七一\n\n例:小雪582=上5中8下2',8,c=C(BT))

# S4: 符头+步骤
s=ns(); bg(s,'符头与演局步骤','日旬首 天盘 人盘 神盘')
rn(s,B,Inches(0.7),Inches(4.5),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(4.3),Inches(0.2),'【日旬首定符头】',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(4.3),Inches(2),
   '日旬首=日支-日干(负加12)\n0甲子上元 10甲戌下元\n8甲申中元 6甲午上元\n4甲辰下元 2甲寅中元\n\n前5位(甲乙丙丁戊)直接使用\n后5位(己庚辛壬癸)推一元\n\n旬空:\n甲子戌亥 甲戌酉申 甲申午未\n甲午辰巳 甲辰寅卯 甲寅子丑',9,c=C(BT))
for i,(st,tl,desc) in enumerate([
    ('4','布地盘','局数宫起戊 阴逆阳顺'),('5','值符值使','旬首原星=值符 原门=值使'),
    ('6','天盘','值符加时干 依次顺转'),('7','人盘','值使加时辰宫 阳顺阴逆'),
    ('8','神盘','值符加天盘符 阳顺阴逆'),('9','旬空','时为主日为辅'),
    ('10','隐干','开门原宫地盘干=开门隐干')]):
    y=Inches(0.7+i*0.75)
    rn(s,Inches(5.2),y,Inches(0.8),Inches(0.6),C(IB))
    tx(s,Inches(5.22),y+Inches(0.02),Inches(0.76),Inches(0.25),f'步{st}',9,c=C(WH),b=True,a=PP_ALIGN.CENTER)
    tx(s,Inches(5.22),y+Inches(0.28),Inches(0.76),Inches(0.25),tl,8,c=C(WH),a=PP_ALIGN.CENTER)
    tx(s,Inches(6.2),y+Inches(0.08),Inches(3.5),Inches(0.45),desc,9,c=C(BT))
rn(s,Inches(10),Inches(0.7),Inches(3),Inches(5.5))
tx(s,Inches(10.08),Inches(0.75),Inches(2.8),Inches(0.2),'三传',9,c=C(IB),b=True)
tx(s,Inches(10.08),Inches(1.0),Inches(2.8),Inches(5),
   '初传(开始)\n地盘值符宫\n\n中传(过程)\n天盘值符宫\n\n末传(结束)\n值使门落宫\n\n三传同宫=伏吟\n初末同宫=反吟\n\n天克地=利客(主动)\n地克天=利主(谨慎)',9,c=C(BT))

# S5: 实例
s=ns(); bg(s,'实例:阴遁5局庚午时','2010.11.25 12:06 庚寅年丁亥月己卯日庚午时')
gc(s,YN5,Inches(0.15),Inches(0.65),Inches(3.8))
tx(s,Inches(4.2),Inches(0.7),Inches(8.5),Inches(5.5),
   '【起局步骤详解】\n1.己卯日 日干己 甲己起甲子\n  从甲子推到午时->庚午时\n2.小雪节气->阴遁\n3.日支4-日干6=-2+12=10甲戌\n  辰戌下元+日后五推->上元5局\n  小雪582 上元5=阴遁5局\n4.布地盘:5宫起戊逆布\n  5戊 4己 3癸 2辛 1壬 9丁 8丙 7庚 6乙\n5.时庚午 时支7-时干7=0甲子\n  戊落中5->天禽值符 死门值使\n6.天禽加时干庚 死门隔6落8宫\n7.旬空:时戌亥空(6宫) 日酉申空(7/2)\n\n三传:初传7宫->中传1宫->末传2宫\n过去值符:甲午辛落8宫(天任=过去趋势)\n将来值符:甲寅癸落6宫(天心=将来趋势)\n12神将布法:月将加值使门 阳顺阴逆',9,c=C(BT))

# S6: 12神将
s=ns(); bg(s,'12神将总论','壬遁法 定将活将 吉凶含义')
for i,(t,d,c2) in enumerate([
    ('子贵神(1)吉','贵人官员钱财',0),('丑天厄(2)凶','暗疾阻碍破财',1),('寅权衡(3)吉','权威权力公检法',0),
    ('卯破损(4)凶','破财开支大方',1),('辰奸私(5)半凶','自私奸诈暗昧',2),('巳文曲(6)吉','聪明好学文书',0),
    ('午天福(7)吉','官方文书酒席',0),('未驿马(8)次吉','变动出行女人',1),('申劳孤(9)半凶','忙碌劳苦孤单',2),
    ('酉性躁(10)凶','生气口舌官司',1),('戌技巧(11)吉','技术艺术五金',0),('亥长寿(12)次吉','拖拉缓慢倔强',2)]):
    x=Inches(0.4+i%4*3.2); y=Inches(0.75+int(i/4)*1.5)
    fi=C(B2) if c2==0 else (C(IV) if c2==1 else None)
    rn(s,x,y,Inches(3),Inches(1.3),fi)
    tx(s,x+Inches(0.08),y+Inches(0.04),Inches(2.8),Inches(0.2),t,9,c=C(IB),b=True)
    tx(s,x+Inches(0.08),y+Inches(0.28),Inches(2.8),Inches(0.9),d,8,c=C(BT))

# S7: 掌诀+隐干
s=ns(); bg(s,'手上掌诀+四种隐干','日=求测人 时=求测事')
rn(s,B,Inches(0.7),Inches(6),Inches(3))
tx(s,B+Inches(0.08),Inches(0.75),Inches(5.8),Inches(0.2),'掌诀:庚寅年十月初五午时占求财',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(5.8),Inches(2.5),
   '1.从寅位起年(庚寅)\n2.从寅起月顺至十月(亥位)\n3.从亥起初一至初五(卯位)\n  卯位=求测人(卯主堵,时运不佳)\n4.从卯起子时至午时(酉位)\n  酉位=求测事(酉主生气不愉快)\n\n结论:逢冲事有变 相克不成',9,c=C(BT))
rn(s,Inches(6.5),Inches(0.7),Inches(6),Inches(3),C(B2))
tx(s,Inches(6.58),Inches(0.75),Inches(5.8),Inches(0.2),'四种隐干',9,c=C(IB),b=True)
tx(s,Inches(6.58),Inches(1.0),Inches(5.8),Inches(2.5),
   '天盘隐干:天盘星原宫地盘干(遗传基因)\n  例:6宫天蓬原1宫辛=隐干辛\n  天盘=现在 原宫=过去\n\n人盘隐干:八门原宫地盘干\n  例:占婚休门隐干辛=家庭问题\n\n暗干:时干加值使门(三角交叉)\n应期干入中:时干加中宫定应期\n  例:时干己加中宫庚落6=庚年庚月',9,c=C(BT))

# S8: 占卜定律
s=ns(); bg(s,'占卜发用定律','年命宫 日干宫 时干宫 用神宫 明宫暗宫')
for i,(t,desc) in enumerate([
    ('年命宫[自身]','年命+坐宫+日干+时干+日支同宫=自身宫\n年命信息大于日干一半'),
    ('日干宫[状态]','日干只代表目前状态\n需与年命/日支/方位/用神重合才准确'),
    ('时干宫[事状]','时干代表目前事情状态不代表结果\n时干+用神同宫才代表求测事'),
    ('用神宫[事本身]','用神+年命日干同宫为准确\n出行开门+地盘年命=开门宫为人宫')]):
    x=B+i*3.15; rn(s,x,Inches(0.7),Inches(3),Inches(1.3),C(B2) if i%2==0 else None)
    tx(s,x+Inches(0.08),Inches(0.75),Inches(2.8),Inches(0.2),t,9,c=C(IB),b=True)
    tx(s,x+Inches(0.08),Inches(1.0),Inches(2.8),Inches(0.9),desc,8,c=C(BT))
rn(s,B,Inches(2.2),Inches(6.3),Inches(3))
tx(s,B+Inches(0.08),Inches(2.25),Inches(6.1),Inches(0.2),'明宫暗宫(临沂投资例)',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(2.5),Inches(6.1),Inches(2.5),
   '年命宫(自身)=明 对宫=暗\n例:临沂先生问投资文具代理\n阴9局 年命庚落1宫\n1宫庚乙同宫休门六合\n表面问投资 实际婚姻感情问题\n对宫9宫景门丁戊=真正投资事\n\n求测事和内在问题在本宫或对宫\n即使对方不问也能知道',9,c=C(BT))
gc(s,Y9,Inches(6.8),Inches(2.3),Inches(3.5))

# S9-10: 六亲
s=ns(); bg(s,'六亲占卜(一)','男命 天干五行')
for i,(t,desc) in enumerate([
    ('妻子','他克不同性\n壬->丁 丙->癸'),('第三者','他克同性\n壬->丙 丙->壬'),
    ('父亲','生他同性\n壬->庚 丙->戊'),('母亲','生他不同性\n壬->辛 丙->己'),
    ('儿子','他生同性\n壬->戊 丙->己'),('女儿','他生不同性\n壬->己 丙->戊'),
    ('官位/领导','克他不同性'),('鬼位/小人/疾','克他同性')]):
    x=B+i%4*3.15; y=Inches(0.7+int(i/4)*1.5)
    rn(s,x,y,Inches(3),Inches(1.3))
    tx(s,x+Inches(0.08),y+Inches(0.04),Inches(2.8),Inches(0.2),t,9,c=C(IB),b=True)
    tx(s,x+Inches(0.08),y+Inches(0.3),Inches(2.8),Inches(0.9),desc,8,c=C(BT))
tx(s,B,Inches(4.0),Inches(12.53),Inches(0.3),'夫妻同宫感情不好 对宫相冲变动 看长相:六亲落宫星门',9,c=C(RA),b=True)

s=ns(); bg(s,'六亲(二)+流年运势','女命 工作/疾病/财运 太岁法则')
rn(s,B,Inches(0.7),Inches(4),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(3.8),Inches(0.2),'女命六亲',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(3.8),Inches(2),
   '丈夫=克她不同性 第三者=克她同性\n母亲=生她同性 父亲=生她不同性\n女儿=她生同性 儿子=她生不同性\n官位=她克不同性 小人=她克同性\n\n工作宫:女她克不同性\n疾病宫:女他克同性\n财运宫:女克他同性\n\n例:男癸年 阳8局\n自身9宫 妻丙1宫 父辛7宫 母庚8宫',9,c=C(BT))
rn(s,Inches(4.5),Inches(0.7),Inches(4),Inches(2.5),C(B2))
tx(s,Inches(4.58),Inches(0.75),Inches(3.8),Inches(0.2),'流年法则',9,c=C(IB),b=True)
tx(s,Inches(4.58),Inches(1.0),Inches(3.8),Inches(2),
   '年命克太岁=有灾(伤灾破财)\n太岁克年命=有灾(较轻)\n太岁生年命=大吉(大胆做)\n年命生太岁=付出大开支大\n年命同太岁=平平\n月干克年命=该月不顺\n\n太岁宫门星=具体事物\n例:白虎伤门=注意车辆道路',9,c=C(BT))
rn(s,Inches(9),Inches(0.7),Inches(4),Inches(2.5))
tx(s,Inches(9.08),Inches(0.75),Inches(3.8),Inches(0.2),'实例',9,c=C(IB),b=True)
tx(s,Inches(9.08),Inches(1.0),Inches(3.8),Inches(2),
   '例1:己巳年局 年命丁(6金)克太岁(3木)\n=付出大不利 月干付出奔波\n明太岁庚比和=平平\n\n例2:1982男壬击刑4宫=不顺\n太岁克年命=小灾\n6戊入墓破财白虎死门血光',8,c=C(BT))

# S11-12: 婚姻+工作
s=ns(); bg(s,'婚姻合婚占卜','合婚 感情判断 实例')
rn(s,B,Inches(0.7),Inches(6),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(5.8),Inches(0.2),'合婚方法',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(5.8),Inches(2),
   '年命相生不落空=好 相克=败局\n伏吟=晚婚 反吟=早婚乱\n乙奇女方 庚为男方\n乙庚同宫/相克=感情不好\n乙下辛=女方要走 庚下丁=男三\n休门=家庭气氛 六合=婚姻整体\n六合落空=感情破裂',9,c=C(BT))
rn(s,Inches(6.5),Inches(0.7),Inches(6),Inches(2.5),C(B2))
tx(s,Inches(6.58),Inches(0.75),Inches(5.8),Inches(0.2),'实例',9,c=C(IB),b=True)
tx(s,Inches(6.58),Inches(1.0),Inches(5.8),Inches(2),
   '青岛男1982(壬)与1988女(戊)\n壬2宫(天蓬辛好色) 戊3宫击刑\n3克2=合婚失败\n男未来看丁(妻星)7宫旺=漂亮\n7空=暂无 填实为婚期\n\n上海1976男+两女\n男9 女丙7(克) 女乙2(生)\n生2宫=合适',9,c=C(BT))

s=ns(); bg(s,'工作占卜','开门 六亲官位 用神 实例')
rn(s,B,Inches(0.7),Inches(6),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(5.8),Inches(0.2),'工作判断',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(5.8),Inches(2),
   '开门被制=压力 门迫=不稳定\n开门落旺=有实力 落空=迷茫\n入墓8宫=没活力\n遇卯酉=找关系 遇午巳=娱乐\n男克他不同性=官 同性=小人\n主客:天克地利客(动) 地克天利主(静)\n用神:公务员休门 技术杜门 店铺开门',9,c=C(BT))
rn(s,Inches(6.5),Inches(0.7),Inches(6),Inches(2.5),C(B2))
tx(s,Inches(6.58),Inches(0.75),Inches(5.8),Inches(0.2),'实例(新疆1984+烟台1978)',9,c=C(IB),b=True)
tx(s,Inches(6.58),Inches(1.0),Inches(5.8),Inches(2),
   '新疆84(甲子)阴5局:戊击刑3宫\n开门3门迫+九天=想动\n官乙9玄武=小人 地盘克天=非时机\n需明年填实 南方求财\n\n烟台78(戊午)阳7局:戊落1坎\n开门7值符=有前途 临太岁=有靠山\n六合空=无贵人 天盘生地=利主\n需等明年1宫填实 谨防小人(末己+玄武)',9,c=C(BT))

# S13: 财运
s=ns(); bg(s,'财运与投资','四看法 七步法 实例')
rn(s,B,Inches(0.7),Inches(6),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(5.8),Inches(0.2),'财运四看+投资七步',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(5.8),Inches(2),
   '一、年命宫(运势根基)\n二、甲子戊(财产整体)\n  戊击刑/戊+辛=破财 戊临壬=困\n三、生门(利润被制不力)\n四、六亲财位(他克同性)\n\n投资七步:\n1.戊(资金)2.生门(利润)3.年命(运气)\n4.六合+合作方5.生戊关系\n6.三传7.主客时机',9,c=C(BT))
rn(s,Inches(6.5),Inches(0.7),Inches(6),Inches(2.5),C(B2))
tx(s,Inches(6.58),Inches(0.75),Inches(5.8),Inches(0.2),'实例',9,c=C(IB),b=True)
tx(s,Inches(6.58),Inches(1.0),Inches(5.8),Inches(2),
   '沈阳1979:阴5局 己8宫开门入墓\n甲子戊4空=财运不力 生门同4空\n壬财7宫玄武天蓬=不稳定小人口舌\n需付出才能得财\n\n临沂投资例:阴9局伏吟=不宜\n戊落空=无资金 年命庚一般\n生门8生7=努力有利润\n三传初末同=头尾一起\n时机不到 先考察到秋分',9,c=C(BT))

# S14: 三传+胎产+择吉
s=ns(); bg(s,'三传用法+胎产+择吉','三传结构 断男女 吉格凶格')
rn(s,B,Inches(0.7),Inches(4),Inches(2.8))
tx(s,B+Inches(0.08),Inches(0.75),Inches(3.8),Inches(0.2),'三传',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(3.8),Inches(2.3),
   '初(地盘值符)->中(天盘值符)->末(值使)\n三传同=伏吟慢 初末同=反吟快\n三传生年命=利 克=不利\n天克地=利客(主动)\n地克天=利主(谨慎)\n末传宫数=结束天数',9,c=C(BT))
rn(s,Inches(4.5),Inches(0.7),Inches(4),Inches(2.8),C(B2))
tx(s,Inches(4.58),Inches(0.75),Inches(3.8),Inches(0.2),'胎产断男女',9,c=C(IB),b=True)
tx(s,Inches(4.58),Inches(1.0),Inches(3.8),Inches(2.3),
   '直接(孕妇问)->看坤宫\n间接(代问)->六亲找宫\n坤宫天盘星阴阳:\n阳星(蓬任冲辅)+阳干=男\n星干不同->改看八门\n例:坤天蓬(阳)+丁(阴)=看休门(阳)=男',9,c=C(BT))
rn(s,Inches(9),Inches(0.7),Inches(4),Inches(2.8))
tx(s,Inches(9.08),Inches(0.75),Inches(3.8),Inches(0.2),'择吉',9,c=C(IB),b=True)
tx(s,Inches(9.08),Inches(1.0),Inches(3.8),Inches(2.3),
   '天遁(丙+生+丁)百事吉\n地遁(乙+开+己)造屋吉\n人遁(太阴+丁+休)万事吉\n龙回首(甲+丙)百事吉\n鸟跌穴(丙+甲)百战胜\n三诈五假出兵嫁娶吉\n\n宝日(干生支)大吉 义日次吉\n五不遇时(时干克日干)=极凶',9,c=C(BT))

# S15: 阳宅
s=ns(); bg(s,'阳宅风水','十维度 青龙白虎')
rn(s,B,Inches(0.7),Inches(6.5),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(6.3),Inches(0.2),'阳宅十维度',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(6.3),Inches(2),
   '1.生门(环境) 2.坐向(九星旺衰)\n3.值使(大门) 4.值符(坐山人丁)\n5.乙奇(青龙男) 6.辛(白虎女)\n7.壬(来水) 8.癸(厕所)\n9.丙(灶) 10.丁(香火)\n\n宫位断地气:\n1宫潮湿有水 2宫土地 3宫乱石\n6宫地脉好 7宫小水流\n8宫山地 9宫采光好',9,c=C(BT))
rn(s,Inches(6.8),Inches(0.7),Inches(6),Inches(2.5),C(B2))
tx(s,Inches(6.88),Inches(0.75),Inches(5.8),Inches(0.2),'青龙白虎+实例',9,c=C(IB),b=True)
tx(s,Inches(6.88),Inches(1.0),Inches(5.8),Inches(2),
   '龙抱虎出知府(青龙高男得力)\n虎抱龙万事凶(白虎高女掌权)\n乙受制=龙砂受损男无发展\n辛+乙白虎猖狂=男不得力\n\n聊城男1977:阴2局\n生门1门迫=潮湿近水人虚弱\n对宫9死门白虎=有坟\n辛4=白虎女权威 壬1帝旺=财运好\n丁6空=无香火(需初一十五烧纸)',9,c=C(BT))

# S16: 阴宅
s=ns(); bg(s,'阴宅风水','九维度 先人保佑')
gc(s,Y8,Inches(0.15),Inches(0.65),Inches(3.8))
tx(s,Inches(4.2),Inches(0.7),Inches(8.5),Inches(5.5),
   '【阴宅九维度】\n1.死门(坟地)2.死门天地盘(先人保佑)\n3.值使(明堂)4.白虎(墓碑)\n5.值符(来龙)6.乙奇(青龙男丁)\n7.辛(白虎女丁)8.壬(来水)\n9.地盘值符(地脉)\n\n先人保佑:地盘生天盘=保佑\n地盘克天盘=不保佑\n墓碑上部损=147房 中=258 下=369\n死门落空=无龙气\n\n【实例:聊城女士 阳8局】\n死门4被制=坟有损 癸击刑水不好\n天芮=后代病 占地脉但没扎准穴\n先人不保佑 来龙无力方向不正\n乙9不秀丽男多口舌 辛4天芮女多病\n壬1空=财运不得力\n白虎开门天心=墓碑完好',9,c=C(BT))

# S17: 灵异+外应+杂占+符箓
s=ns(); bg(s,'灵异怪病+外应+杂占+符箓','阴煞 118种外应 考试走失 四纵五横')
rn(s,B,Inches(0.7),Inches(4),Inches(2.5))
tx(s,B+Inches(0.08),Inches(0.75),Inches(3.8),Inches(0.2),'阴煞符号',9,c=C(IB),b=True)
tx(s,B+Inches(0.08),Inches(1.0),Inches(3.8),Inches(2),
   '螣蛇(蛇精) 玄武(黄鼠狼)\n太阴(阴魂) 白虎(凶神)\n九地(土地爷) 九天(天神)\n值符(神灵佑) 六合(家仙)\n年命临死门=与死人有关\n年命落1宫=鬼位阴气重\n年命乘癸=体弱招邪',9,c=C(BT))
rn(s,Inches(4.5),Inches(0.7),Inches(4.3),Inches(2.5),C(B2))
tx(s,Inches(4.58),Inches(0.75),Inches(4.1),Inches(0.2),'外应+杂占+符箓',9,c=C(IB),b=True)
tx(s,Inches(4.58),Inches(1.0),Inches(4.1),Inches(2),
   '外应:直接(即结论)+间接(入局分析)\n共118种(云开见日 乌鸦灾鹊喜等)\n\n考试:天芮+天辅+丁\n走失:年命(平安)+六合(方位)\n疾病:年命+天芮(病因)\n凶杀:死门+庚(凶手位置)\n\n四纵五横:黄纸朱砂书符\n咒:天地定位八方先师到\n天无忌地无忌百无禁忌',9,c=C(BT))

# END
s=ns()
r=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(2),Inches(2),Inches(9.33),Inches(3))
r.fill.solid(); r.fill.fore_color.rgb=C(IB); r.line.fill.background()
tx(s,Inches(2.5),Inches(2.3),Inches(8.33),Inches(1),'感谢聆听 学有所成',30,c=C(WH),b=True,a=PP_ALIGN.CENTER)
tx(s,Inches(2.5),Inches(3.3),Inches(8.33),Inches(0.5),'真传一句话 假传万卷书',14,c=RGBColor(0xCC,0xCC,0xDD),a=PP_ALIGN.CENTER)

n=len(prs.slides)
prs.save('e:\\wenan catch\\成慈高级奇门讲义_高密度版.pptx')
print(f'DONE: {n} slides total')
