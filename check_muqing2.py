"""检查木清当前状态"""
import sqlite3
conn = sqlite3.connect("data/wenan_catch.db")
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT task_status, transcribed_text, ai_refined_text,
           substr(video_desc, 1, 60) as desc_preview,
           video_url
    FROM posts
    WHERE source_target='木清'
    ORDER BY collected_at DESC
""").fetchall()

print(f"木清: {len(rows)} 条\n")
for r in rows:
    print(f"  status={r['task_status']}")
    print(f"  asr={'有' if r['transcribed_text'] else '无'} ({len(r['transcribed_text'] or '')}字)")
    print(f"  ai={'有' if r['ai_refined_text'] else '无'} ({len(r['ai_refined_text'] or '')}字)")
    print(f"  url={'有' if r['video_url'] else '无'}")
    if r['transcribed_text']:
        print(f"  内容: {r['transcribed_text'][:80]}...")
    elif r['desc_preview']:
        print(f"  desc: {r['desc_preview']}...")
    print()

conn.close()
