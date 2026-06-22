"""Join candidates + labels -> balanced, length-diverse, single labeled CSV.

- Balance: downsample each class to N_PER_CLASS, picking a length-diverse spread so
  length is not a giveaway for the label (reaction is naturally short, analysis long).
- Output: ONE complete labeled file (text, label, note) -- NOT pre-split. The Colab
  notebook does the 70/15/15 train/val/test split automatically.
- Scrub: replace u/username mentions so no usernames ship in the committed CSV.
"""
import csv, json, random, re

N_PER_CLASS = 70
SEED = 13
random.seed(SEED)

cands = {c["idx"]: c for c in json.load(open("candidates.json"))}
labels = json.load(open("labels.json"))
LABEL_ID = {"analysis": 0, "hot_take": 1, "reaction": 2}

# join
rows = []
for idx, lab in labels.items():
    c = cands[int(idx)]
    rows.append({
        "id": c["id"], "text": re.sub(r"/?u/[A-Za-z0-9_-]+", "u/[user]", c["text"]),
        "score": c["score"], "char_len": c["len"],
        "label": lab["label"], "note": lab.get("note", ""),
    })

by_class = {k: [r for r in rows if r["label"] == k] for k in LABEL_ID}
print("labeled pool:", {k: len(v) for k, v in by_class.items()})


def length_diverse(items, n):
    """Pick n items spread evenly across the length range."""
    s = sorted(items, key=lambda r: r["char_len"])
    if len(s) <= n:
        return s
    picks = sorted({round(i * (len(s) - 1) / (n - 1)) for i in range(n)})
    # if rounding collided, backfill from the rest
    chosen = [s[i] for i in picks]
    extra = [r for r in s if r not in chosen]
    random.shuffle(extra)
    while len(chosen) < n:
        chosen.append(extra.pop())
    return chosen[:n]


selected = []
for k in LABEL_ID:
    selected += [(r, k) for r in length_diverse(by_class[k], N_PER_CLASS)]

# single complete labeled file -- NOT pre-split (the notebook splits 70/15/15)
final = [r for r, _ in selected]
random.shuffle(final)

cols = ["text", "label", "note"]            # the three columns the notebook needs
with open("takemeter_dataset.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in final:
        w.writerow(r)

# report
from collections import Counter
import statistics
c = Counter(r["label"] for r in final); n = len(final)
print(f"\nwrote takemeter_dataset.csv  ({n} rows, single unsplit file: {cols})")
for k in LABEL_ID:
    print(f"  {k:8s}: {c[k]} ({100*c[k]/n:.0f}%)")
print(f"  max label share: {100*max(c.values())/n:.0f}%  (must be < 70%)")
for k in LABEL_ID:               # length sanity: classes should overlap, not separate cleanly
    ls = sorted(r["char_len"] for r in final if r["label"] == k)
    print(f"  {k:8s} char_len  min {ls[0]:4d}  median {int(statistics.median(ls)):4d}  max {ls[-1]:4d}")
