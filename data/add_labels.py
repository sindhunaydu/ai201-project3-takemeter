"""Merge a batch of labels into labels.json.  Usage: python3 add_labels.py '<json>'
Input JSON: {"<idx>": "label", "<idx>": "label#borderline note", ...}
label in {analysis, hot_take, reaction}.  '#' marks a borderline case + note.
"""
import json, sys, os
from collections import Counter

batch = json.loads(sys.argv[1])
db = json.load(open("labels.json")) if os.path.exists("labels.json") else {}
valid = {"analysis", "hot_take", "reaction"}
for k, v in batch.items():
    lab, _, note = v.partition("#")
    lab = lab.strip()
    assert lab in valid, f"bad label {lab!r} for idx {k}"
    db[str(k)] = {"label": lab, "borderline": bool(note), "note": note.strip()}
json.dump(db, open("labels.json", "w"), indent=2)
c = Counter(v["label"] for v in db.values())
print(f"labeled total: {len(db)}  | analysis {c['analysis']}  hot_take {c['hot_take']}  reaction {c['reaction']}  | borderline {sum(v['borderline'] for v in db.values())}")
