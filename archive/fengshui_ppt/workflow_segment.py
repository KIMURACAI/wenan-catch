export const meta = {
  name: 'resegment-pages',
  description: '重排 151 页 PPT 正文分段：按 PDF 坐标拼接断行，输出每页重排后段落',
  phases: [{ title: '重排', detail: '每页一个 agent 重排分段' }],
}

const PAGES = args;  // [{slide, pdf_page, ppt_boxes, pdf_body_blocks}]

const SEG_SCHEMA = {
  type: 'object',
  properties: {
    slide: { type: 'number' },
    paragraphs: {
      type: 'array',
      items: { type: 'string' },
      description: '重排后的完整段落列表，每个元素是一段完整文字'
    },
    notes: { type: 'string', description: '处理说明' }
  },
  required: ['slide', 'paragraphs']
}

const results = await parallel(PAGES.map(page => () => {
  const body = page.pdf_body_blocks
    .filter(b => b.text_type === 'body')
    .map(b => `[y=${Math.round(b.y)}] ${b.text}`)
    .join('\n')
  const prompt = `你是中文排版专家。下面是一页风水教材 PDF 提取的正文文字块，按它们在页面上的纵向位置（y坐标）排序。

任务：把这些被 PDF 断行的碎片拼接成正确的完整段落。
规则：
1. 严格按 y 顺序拼接，不要打乱顺序
2. 行尾没有句号时，说明下一行是同一句的延续，要拼接
3. 行尾是句号、问号、感叹号时，该段结束，另起一段
4. 保留所有文字内容，不增删改任何字
5. 如果是标题（如"一、风水学的概论"），单独成段
6. 合并后去掉行间多余空格，但保留原文用词（包括"  "空格和错别字，不修正）

正文块：
${body}

请只返回重排后的段落列表。`
  return agent(prompt, { label: `slide-${page.slide}`, phase: '重排', schema: SEG_SCHEMA })
}))

return results.filter(Boolean)
