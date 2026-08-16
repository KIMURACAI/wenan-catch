"""查看转录文案内容"""
import sqlite3

conn = sqlite3.connect(r"E:\wenan catch\data\wenan_catch.db")
rows = conn.execute("""
    SELECT post_id, transcribed_text, transcribe_status
    FROM posts
    WHERE transcribe_status='completed' AND transcribed_text!=''
""").fetchall()

print(f"已识别 {len(rows)} 条文案:\n")
for i, r in enumerate(rows, 1):
    text = r[1]
    print(f"--- 文案 #{i} ({len(text)}字) ---")
    print(text[:200])
    print()

conn.close()
