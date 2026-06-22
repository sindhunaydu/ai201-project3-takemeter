"""Filter + dedupe + bucket the raw pool into an ordered candidate list for labeling.

Order = long -> medium -> short, so the scarce high-substance comments (where
`analysis` and `hot_take` concentrate) get a stable low idx and are labeled first.
"""
import json, re, html

raw = json.load(open("raw_comments.json"))
JUNK = {"[deleted]", "[removed]", ""}

def norm(b):
    b = html.unescape(b or "")
    b = re.sub(r"\s+", " ", b).strip()
    return b

seen_ids, seen_txt, cands = set(), set(), []
for c in raw:
    cid = c.get("id")
    t = norm(c.get("body", ""))
    if cid in seen_ids:
        continue
    if t in JUNK or len(t) < 2 or t.startswith("http"):
        continue
    key = t.lower()
    if key in seen_txt:           # drop exact-duplicate copypasta/bot text
        continue
    seen_ids.add(cid); seen_txt.add(key)
    cands.append({"id": cid, "text": t, "len": len(t), "score": c.get("score")})

def bucket(n):
    return "long" if n >= 320 else ("medium" if n >= 70 else "short")

order = {"long": 0, "medium": 1, "short": 2}
cands.sort(key=lambda c: (order[bucket(c["len"])], -c["len"]))
for i, c in enumerate(cands, 1):
    c["idx"] = i
    c["bucket"] = bucket(c["len"])

json.dump(cands, open("candidates.json", "w"), indent=2)
from collections import Counter
b = Counter(c["bucket"] for c in cands)
print(f"usable candidates: {len(cands)} of {len(raw)}")
print(f"buckets -> long(>=320): {b['long']}  medium(70-319): {b['medium']}  short(<70): {b['short']}")
print("idx ranges:",
      f"long 1..{b['long']}",
      f"medium {b['long']+1}..{b['long']+b['medium']}",
      f"short {b['long']+b['medium']+1}..{len(cands)}")
