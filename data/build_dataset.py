"""Join candidates + labels -> balanced, length-diverse, stratified-split dataset CSV.

- Balance: downsample each class to N_PER_CLASS, picking a length-diverse spread so
  length is not a giveaway for the label (reaction is naturally short, analysis long).
- Split: stratified 70/15/15 so every split has the same class balance.
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

# stratified split per class: 70/15/15
final = []
for k in LABEL_ID:
    items = [r for r, kk in selected if kk == k]
    random.shuffle(items)
    n = len(items); n_test = round(0.15 * n); n_val = round(0.15 * n)
    for i, r in enumerate(items):
        split = "test" if i < n_test else ("val" if i < n_test + n_val else "train")
        r = dict(r)
        r.update({"label_id": LABEL_ID[k], "pre_label": k, "final_label": k,
                  "pre_labeled": True, "changed": False, "split": split})
        final.append(r)
random.shuffle(final)

cols = ["id", "text", "label", "label_id", "score", "char_len",
        "pre_label", "final_label", "pre_labeled", "changed", "note", "split"]
with open("takemeter_dataset.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in final:
        w.writerow({c: r[c] for c in cols})

# report
from collections import Counter
print(f"\nwrote takemeter_dataset.csv  ({len(final)} rows)")
for sp in ["train", "val", "test"]:
    c = Counter(r["label"] for r in final if r["split"] == sp)
    print(f"  {sp:5s} ({sum(c.values()):3d}): analysis {c['analysis']}  hot_take {c['hot_take']}  reaction {c['reaction']}")
# length sanity: median length per class (should overlap, not be cleanly separable)
import statistics
for k in LABEL_ID:
    ls = sorted(r["char_len"] for r in final if r["label"] == k)
    print(f"  {k:8s} char_len  min {ls[0]:4d}  median {int(statistics.median(ls)):4d}  max {ls[-1]:4d}")
