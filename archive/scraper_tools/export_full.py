"""导出完整转写结果"""
import sqlite3

conn = sqlite3.connect(r"E:\wenan catch\data\wenan_catch.db")
rows = conn.execute("""
    SELECT source_target, transcribed_text
    FROM posts
    WHERE transcribe_status='completed' AND transcribed_text!=''
    ORDER BY source_target, LENGTH(transcribed_text) DESC
""").fetchall()
conn.close()

with open(r"e:\wenan catch\转写结果_完整版.txt", "w", encoding="utf-8") as f:
    current_target = ""
    for i, r in enumerate(rows, 1):
        target = r[0]
        text = r[1].strip()
        if target != current_target:
            f.write(f"\n{'='*50}\n")
            f.write(f"📋 {target}\n")
            f.write(f"{'='*50}\n\n")
            current_target = target
        f.write(f"#{i}\n")
        f.write(text + "\n\n")

print(f"导出 {len(rows)} 条文案")
print(f"文件: 转写结果_完整版.txt")
