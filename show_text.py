"""输出文案到文件（避免终端乱码）"""
import sqlite3

conn = sqlite3.connect(r"E:\wenan catch\data\wenan_catch.db")
rows = conn.execute("""
    SELECT post_id, transcribed_text, video_desc
    FROM posts
    WHERE transcribe_status='completed' AND transcribed_text!=''
    ORDER BY LENGTH(transcribed_text) DESC
""").fetchall()
conn.close()

with open("转写结果.txt", "w", encoding="utf-8") as f:
    f.write(f"共 {len(rows)} 条转写结果\n")
    f.write("=" * 50 + "\n\n")
    for i, r in enumerate(rows, 1):
        f.write(f"--- #{i} ({len(r[1])}字) ---\n")
        f.write(r[1].strip() + "\n\n")

print(f"已写入 {len(rows)} 条文案到 转写结果.txt")
print(f"用记事本或VS Code打开就能看")
