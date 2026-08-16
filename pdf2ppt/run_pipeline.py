"""
PDF → 横版 PPT 完整流水线主控

用法:
  python pdf2ppt/run_pipeline.py "漫画.pdf"                    # 全流程
  python pdf2ppt/run_pipeline.py "漫画.pdf" --from 3           # 从 Stage 3 续跑
  python pdf2ppt/run_pipeline.py "漫画.pdf" --clean-mode llm   # Stage 4 用 LLM
"""
import os, sys, json, argparse
from pathlib import Path

HERE = Path(__file__).parent


def stage1_extract(pdf_path, work_dir, min_img=150):
    print("\n" + "="*60)
    print("Stage 1 · 提取 PDF 内容")
    print("="*60)
    out = os.path.join(work_dir, "comic_page_models.json")
    from pdf2ppt.extract import extract_all_pages
    pages = extract_all_pages(pdf_path, min_img_dim=min_img)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    print(f"已保存: {out}")
    return out


def stage2_build(pdf_path, page_json, work_dir, img_dir, title, author):
    print("\n" + "="*60)
    print("Stage 2 · 生成初步 PPT")
    print("="*60)
    from pdf2ppt.build_ppt import build_ppt
    from pdf2ppt.export_images import has_user_images, export_embedded
    if not has_user_images(img_dir):
        print("未找到手裁图，导出 PDF 内嵌图作为配图")
        export_embedded(pdf_path, page_json, img_dir)
    out = os.path.join(work_dir, "output_raw.pptx")
    build_ppt(page_json, out, img_dir, title, author)
    return out


def stage3_bind(page_json, raw_pptx, work_dir):
    print("\n" + "="*60)
    print("Stage 3 · PPT↔PDF 绑定")
    print("="*60)
    out = os.path.join(work_dir, "slide_pdf_binding.json")
    from pdf2ppt.binding import build_binding
    build_binding(page_json, raw_pptx, out)
    return out


def stage4_clean(binding_json, work_dir, mode):
    print("\n" + "="*60)
    print("Stage 4 · 清理对话 + 重排正文")
    print("="*60)
    out = os.path.join(work_dir, "cleaned_paragraphs.json")
    if mode == "rule":
        from pdf2ppt.clean import clean_rule
        clean_rule(binding_json, out)
    else:
        # LLM 模式：准备批次，提示用 Workflow 处理
        from pdf2ppt.clean import clean_llm
        parts = clean_llm(binding_json, out, batches=8,
                          work_dir=os.path.join(work_dir, "seg_batches"))
        print("\nLLM 模式需要手动运行 Workflow 清理，然后合并结果到 cleaned_paragraphs.json")
        print("批次文件已生成，参考 pdf2ppt/workflow_clean.js")
        return None
    return out


def stage5_layout(raw_pptx, cleaned_json, work_dir):
    print("\n" + "="*60)
    print("Stage 5 · 应用文字 + 图片排版")
    print("="*60)
    out = os.path.join(work_dir, "output_final.pptx")
    from pdf2ppt.layout import apply_and_layout
    apply_and_layout(raw_pptx, cleaned_json, out)
    return out


def main():
    parser = argparse.ArgumentParser(description="PDF → 横版 PPT 流水线")
    parser.add_argument("pdf", help="源 PDF 路径")
    parser.add_argument("--from", dest="from_stage", type=int, default=1,
                        help="起始阶段 (1-5)")
    parser.add_argument("--workdir", default="", help="工作目录（默认 PDF 旁）")
    parser.add_argument("--imgdir", default="_user_images",
                        help="用户裁切图目录（slide001_img01.png 命名）")
    parser.add_argument("--clean-mode", default="rule", choices=["rule", "llm"],
                        help="Stage 4 清理模式")
    parser.add_argument("--title", default="", help="封面标题")
    parser.add_argument("--author", default="", help="封面作者")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"文件不存在: {args.pdf}")
        sys.exit(1)

    # 工作目录
    work_dir = args.workdir or os.path.dirname(os.path.abspath(args.pdf))
    os.makedirs(work_dir, exist_ok=True)
    img_dir = args.imgdir if os.path.isabs(args.imgdir) else os.path.join(work_dir, args.imgdir)

    # 各阶段文件路径
    page_json = os.path.join(work_dir, "comic_page_models.json")
    raw_pptx = os.path.join(work_dir, "output_raw.pptx")
    binding_json = os.path.join(work_dir, "slide_pdf_binding.json")
    cleaned_json = os.path.join(work_dir, "cleaned_paragraphs.json")
    final_pptx = os.path.join(work_dir, "output_final.pptx")

    # 阶段性执行（支持断点续跑）
    if args.from_stage <= 1:
        page_json = stage1_extract(args.pdf, work_dir)
    else:
        print(f"跳过 Stage 1，使用: {page_json}")
        if not os.path.exists(page_json):
            print("找不到 comic_page_models.json"); sys.exit(1)

    if args.from_stage <= 2:
        raw_pptx = stage2_build(args.pdf, page_json, work_dir, img_dir, args.title, args.author)
    else:
        print(f"跳过 Stage 2，使用: {raw_pptx}")

    if args.from_stage <= 3:
        binding_json = stage3_bind(page_json, raw_pptx, work_dir)
    else:
        print(f"跳过 Stage 3，使用: {binding_json}")

    if args.from_stage <= 4:
        cleaned_json = stage4_clean(binding_json, work_dir, args.clean_mode)
    else:
        print(f"跳过 Stage 4，使用: {cleaned_json}")

    if cleaned_json and os.path.exists(cleaned_json):
        if args.from_stage <= 5:
            final_pptx = stage5_layout(raw_pptx, cleaned_json, work_dir)
    else:
        print("cleaned_paragraphs.json 不存在，无法执行 Stage 5")

    print("\n" + "="*60)
    print("流水线完成")
    print(f"  最终文件: {final_pptx if os.path.exists(final_pptx) else '（未生成）'}")
    print(f"  中间数据: {work_dir}")
    print("="*60)


if __name__ == "__main__":
    # 直接以脚本方式运行（python pdf2ppt/run_pipeline.py）时，
    # 把项目根目录加入 sys.path，保证 pdf2ppt 包可导入
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
