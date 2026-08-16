"""导出润色后文案到桌面

格式：
  作者名
  （每条文案下方标注日期）
"""
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DB = Path(r"E:\wenan catch\data\wenan_catch.db")
OUTPUT_DIR = Path.home() / "Desktop" / "抖音文案采集" / "文案"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT source_target, ai_refined_text, transcribed_text, video_desc, video_title,
           collected_at, publish_time
    FROM posts
    WHERE (ai_refined_text != '' OR transcribed_text != '' OR video_desc != '')
    ORDER BY source_target, collected_at DESC
""").fetchall()
conn.close()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
by_target = defaultdict(list)
for r in rows:
    by_target[r["source_target"]].append(r)

for target, posts in by_target.items():
    filepath = OUTPUT_DIR / f"{target}_{today}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        # 标题只出现一次
        f.write(f"{target}\n\n")

        for i, p in enumerate(posts, 1):
            text = p["ai_refined_text"] or p["transcribed_text"] or p["video_desc"] or p["video_title"]
            # 去除标签和链接
            import re
            text = re.sub(r'#\S+', '', text)
            text = re.sub(r'@\S+', '', text)
            text = re.sub(r'https?://\S+', '', text)
            text = text.strip().strip('#@，。！？：；,.:;!? ')
            text = re.sub(r'\s+', '', text)  # 合并多余空白

            # 过滤纯标签/无意义内容
            clean_check = re.sub(r'[^一-鿿]', '', text)
            if len(clean_check) < 4:
                continue  # 跳过无有效内容的条目

            # 日期：优先用发布时间，否则用采集时间
            date = ""
            if p["publish_time"]:
                date = p["publish_time"][:10]
            elif p["collected_at"]:
                date = p["collected_at"][:10]

            f.write(f"{text}\n")
            if date:
                f.write(f"{date}\n")
            f.write("---\n\n")

    print(f"  {target}: {len(posts)} 条 → {filepath}")

print(f"\n完成！共 {len(rows)} 条")
