"""
Stage 4 补充 · 合并 LLM workflow 结果到 cleaned_paragraphs.json
在 workflow_clean.js 运行完成后调用。

用法:
  python pdf2ppt/merge_workflow.py <journal.jsonl> -o cleaned_paragraphs.json
"""
import json, argparse


def merge(journal_path, output_path):
    results_by_slide = {}
    with open(journal_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get('type') != 'result':
                continue
            value = rec.get('value') or rec.get('result')
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    continue
            if not isinstance(value, dict):
                continue
            pages = value.get('pages') or value.get('result', {}).get('pages')
            if not pages:
                continue
            for p in pages:
                if 'slide' in p:
                    results_by_slide[p['slide']] = p.get('paragraphs', [])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_by_slide, f, ensure_ascii=False, indent=1)
    total = sum(len(v) for v in results_by_slide.values())
    print(f"合并完成: {len(results_by_slide)} 页, {total} 段 → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="合并 workflow 结果")
    parser.add_argument("journal", help="workflow journal.jsonl 路径")
    parser.add_argument("-o", "--output", default="cleaned_paragraphs.json")
    args = parser.parse_args()
    merge(args.journal, args.output)
