import json

with open(r"e:\wenan catch\qimen_cases.json", "r", encoding="utf-8") as f:
    d = json.load(f)

# 收集所有文本块
blocks = []
for p in d["preface"]["bio"]:
    blocks.append(p)
for p in d["preface"]["theory"]:
    blocks.append(p)
for s in d["sections"]:
    blocks.append(s["title"])
    for p in s["intro"]:
        blocks.append(p)
    for c in s["cases"]:
        blocks.append(c["title"])
        for p in c["analysis"]:
            blocks.append(p)

full = "\n".join(blocks)
print(f"总字符(去重后块): {sum(len(b) for b in blocks)}")
print(f"唯一文本块数: {len(blocks)}")

# 关键内容抽查
checks = {
    "简介-师传李锦泉": "师传李锦泉奇门师父",
    "主客歌": "天盘动用占为客",
    "案例1-脑部循环": "脑部血液循环",
    "案例10-王星宇对话": "王星宇",
    "卡扎菲": "卡扎菲",
    "婚纱照-七张": "婚纱照",
    "生门得地": "生门得地" if "生门得地" in full else "生门",
    "棋牌-3000元": "3000元",
    "投稿-7万册": "7万册",
}
for name, kw in checks.items():
    print(f"  {'✓' if kw in full else '✗'} {name}: {'在' if kw in full else '缺失'}")

# 检查是否有重复段落（完整重复）
from collections import Counter
cnt = Counter(b for b in blocks if len(b) > 30)
dups = [k for k, v in cnt.items() if v > 1]
print(f"\n重复长段落: {len(dups)} 处")
for dd in dups[:5]:
    print(f"  重复×{cnt[dd]}: {dd[:40]}...")
