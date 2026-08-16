"""
Stage 4 · 清理漫画对话 + 重排正文
基于 slide_pdf_binding.json，逐页：
- 删除漫画人物对话（口语第一人称台词）
- 删除罗盘/图注标注碎片
- 按 PDF 坐标把断行拼回完整段落

两种模式：
- rule: 纯规则（无需 API，快，但判断较粗）
- llm: 调用 LLM 逐批语义判断（准确，需 API key）

输出: cleaned_paragraphs.json
"""
import json, os

# ── 漫画对话特征词（rule 模式用）──
DIALOGUE_HINTS = ["我是", "我们", "怪不得", "原来是这样", "我要", "我想",
                  "啦", "吧！", "呀", "你住", "我家", "我的", "你家的",
                  "他家的", "这里住", "看风水", "师父", "老板", "老公",
                  "老婆", "女儿", "儿子", "这家", "这座", "这个房子"]

try:
    from pdf2ppt.labels import LABEL_CHARS
except ImportError:
    from labels import LABEL_CHARS


def is_roster_label(text):
    """判断是否为罗盘/图注标注碎片"""
    t = text.strip()
    if not t: return True
    if t.isdigit() and len(t) <= 3: return True
    if len(t) <= 8 and all(c in LABEL_CHARS for c in t):
        return True
    return False


def is_dialogue(text):
    """判断是否为漫画对话（口语）"""
    t = text.strip()
    if len(t) > 60: return False  # 长句不太可能是对话
    if not t.endswith(('。', '？', '！', '啦', '呢', '啊', '呀', '吧')):
        # 短句且无句末标点 → 可能是标注
        return False
    score = sum(1 for h in DIALOGUE_HINTS if h in t)
    return score >= 1


def resegment_by_punct(blocks):
    """按句号把断行拼接成段落（rule 模式核心）"""
    paragraphs = []
    current = ''
    for b in blocks:
        text = b['text'].strip()
        if not text: continue
        if is_roster_label(text):
            continue
        if is_dialogue(text):
            continue
        if current and not current.endswith(('。', '！', '？')):
            current += text
        else:
            if current.strip():
                paragraphs.append(current.strip())
            current = text
    if current.strip():
        paragraphs.append(current.strip())
    return paragraphs


def clean_rule(binding_path, output_path):
    """纯规则模式（实验性，质量不足，仅无 LLM 时兜底）"""
    print("[警告] rule 模式质量不足：会漏删无标点图注、糊掉表格、粘合标题。")
    print("        建议用 --clean-mode llm（需跑 workflow_clean.js）。")
    binding = json.load(open(binding_path, 'r', encoding='utf-8'))
    results = {}
    for key, entry in binding.items():
        snum = int(key.split('_')[1])
        blocks = entry.get('pdf_text_with_pos', [])
        # 只保留 body 类型（heading 另处理）
        body_blocks = [b for b in blocks if b.get('text_type') == 'body']
        # 保留标题（单独成段）
        heading_blocks = [b for b in blocks if b.get('text_type') == 'heading']
        paras = [h['text'].strip() for h in heading_blocks if h['text'].strip()]
        paras += resegment_by_punct(body_blocks)
        results[snum] = paras

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    total = sum(len(v) for v in results.values())
    print(f"规则清理完成: {len(results)} 页, {total} 段")
    return results


def clean_llm(binding_path, output_path, batches=None, work_dir="seg_batches"):
    """LLM 模式：分批复用 workflow 处理。
    由 run_pipeline.py 通过 Workflow 调用，这里只准备批次。
    """
    binding = json.load(open(binding_path, 'r', encoding='utf-8'))
    os.makedirs(work_dir, exist_ok=True)

    # 构建每页输入
    pages_data = []
    for key, entry in binding.items():
        snum = int(key.split('_')[1])
        body_blocks = [{
            "text": b.get('text', ''),
            "y": (b.get('bbox') or [0, 0])[1] if len(b.get('bbox', [])) >= 2 else 0,
            "text_type": b.get('text_type', 'body'),
        } for b in entry.get('pdf_text_with_pos', [])]
        pages_data.append({
            "slide": snum,
            "pdf_page": entry.get('pdf_page'),
            "pdf_body_blocks": body_blocks,
            "ppt_text": entry.get('ppt_text', ''),
        })

    # 分 N 批
    N = batches or 8
    batch_size = (len(pages_data) + N - 1) // N
    part_info = []
    for i in range(N):
        batch = pages_data[i*batch_size:(i+1)*batch_size]
        if not batch: continue
        path = os.path.join(work_dir, f"part_{i}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(batch, f, ensure_ascii=False, indent=1)
        slides = [p['slide'] for p in batch]
        part_info.append({"index": i, "path": path,
                          "first_slide": slides[0], "last_slide": slides[-1]})

    print(f"已准备 {N} 批数据: {work_dir}")
    print("在 workflow 中运行后，将结果合并到 cleaned_paragraphs.json")
    return part_info


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stage 4: 清理+重排")
    parser.add_argument("binding", help="slide_pdf_binding.json")
    parser.add_argument("-o", "--output", default="cleaned_paragraphs.json")
    parser.add_argument("--mode", default="rule", choices=["rule", "llm"])
    parser.add_argument("--batches", type=int, default=8)
    args = parser.parse_args()

    if args.mode == "rule":
        clean_rule(args.binding, args.output)
    else:
        clean_llm(args.binding, args.output, batches=args.batches)
