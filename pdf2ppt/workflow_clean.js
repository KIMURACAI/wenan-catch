/**
 * Stage 4 · LLM 清理模式（workflow）
 * 逐批读取 seg_batches/part_N.json，语义判断删除对话/标注，拼接正文。
 * 运行后合并各 agent 结果到 cleaned_paragraphs.json。
 *
 * 用法（在 run_pipeline.py --clean-mode llm 后手动调用）：
 *   Workflow({scriptPath: 'pdf2ppt/workflow_clean.js', args: [批次信息]})
 */
export const meta = {
  name: 'clean-resegment',
  description: '逐页重排正文并过滤漫画对话和罗盘标注',
  phases: [{ title: '清理' }],
}

const PARTS = args  // [{index, path, first_slide, last_slide}]

const SCHEMA = {
  type: 'object',
  properties: {
    pages: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          slide: { type: 'number' },
          paragraphs: { type: 'array', items: { type: 'string' } }
        },
        required: ['slide', 'paragraphs']
      }
    }
  },
  required: ['pages']
}

const results = await parallel(PARTS.map(part => () =>
  agent(
    `你是中文排版专家。请读取批次文件 ${part.path}（JSON，包含 slide ${part.first_slide}-${part.last_slide} 的风水教材内容）。

每个页对象包含：
- slide: 页码
- pdf_body_blocks: PDF 提取的文字块，按 y 坐标排序，每块含 text/y/text_type

任务：对每个 slide，输出该页**应保留的正文段落**。
判断规则：
1. 【保留】教学/参考正文：书面语、连贯论述、知识讲解、格局描述
2. 【删除】漫画人物对话：第一人称口语台词（"我是皇帝…""怪不得…""原来是这样…""我要…""我们…"）、感叹语气（"啦/吧/呀"）、人物互问互答
3. 【删除】罗盘/图注标注碎片：单字或几个字（"丁午丙""壬子癸""朱雀""白虎""池塘""湖泊""厂房""店铺"等）、图形标签
4. 【删除】页眉书名和页码（任何书的书名）
5. 【拼接】同一段正文被 PDF 断行的碎片按 y 顺序拼回完整段落（行尾无句号则续接下一行）
6. 【保留】保留所有正文文字，不增删改任何一个字；只删对话/标注/页眉页码
7. 【标题】正文的小标题（"一、""（一）""1、""2、""中国XX时代"）单独成段，保留
8. 【顺序】严格按页面 y 坐标顺序排列段落
9. 【分段粒度】每个编号项/格局条目独立成段。例如"1 楼、6 楼属…"、"2 楼、7 楼属…"、"（1）狮子一定要两个搭配"等，每个编号开头的内容单独一段；以【 】括起的条目（如【戊+乙】、【丙+辛】）也是一条独立段，不要把相邻条目拼接在一起
10. 【表格】表格类内容（如"上元/中元/下元"、"一运1864-1883水"）每个单元格单独一段，不要拼接
11. 【格局条目结构】对形如"【X+Y】…《本旨描述》：…析之：…★注：…"的奇门格局条目：整条【X+Y】从开头到其后的描述/分析/注释**合成一个完整段落**保留（若该页能容下），不要拆散；相邻的【X+Y】条目之间必须断开

输出 JSON 格式：
{"pages": [{"slide": 页码, "paragraphs": ["完整段落1", "完整段落2", ...]}, ...]}
每个 slide 都要输出，即使 paragraphs 为空数组。`,
    { label: `part-${part.index}`, phase: '清理', schema: SCHEMA, effort: 'high' }
  )
))

return results.filter(Boolean)
