# TakeMeter 📺 — Discourse-Quality Classifier for r/television

TakeMeter is a fine-tuned text classifier that scores the **quality of a take** in
[r/television](https://www.reddit.com/r/television/) — sorting comments by how much
they actually *argue* an opinion about TV, rather than just asserting or emoting one.

> TakeMeter classifies comments in **r/television** by discourse quality along a
> single spine — how much a comment actually argues its take: **`analysis`** (a TV
> claim backed by checkable specifics like ratings, episode counts, or plot events),
> **`hot_take`** (a confident judgment asserted with no real support), and
> **`reaction`** (expressive or social comments — jokes, agreement, one-liners — that
> argue nothing). The distinction matters because the community itself polices it:
> regulars reward takes that are "backed up" and dismiss low-effort hot takes and
> circle-jerk reactions, so the labels track a quality line people there already care
> about.

## Project status

| Milestone | Deliverable | Status |
|---|---|---|
| M1 | Community + label taxonomy | ✅ done — see [`planning.md`](planning.md) |
| M2 | ≥200 labeled comments, train/val/test split | ⏳ pending |
| M3 | Fine-tune `distilbert-base-uncased` (Colab T4) | ⏳ pending |
| M4 | Zero-shot baseline (`llama-3.3-70b-versatile` via Groq) | ⏳ pending |
| M5 | Evaluation report (accuracy, per-class F1, confusion matrix, error analysis) | ⏳ pending |

---

## The labels

The whole taxonomy hangs on one question: **how much does the comment do to support a
take about TV?**

| label | one-line definition |
|---|---|
| **`analysis`** | An evaluative/interpretive claim about TV backed by ≥1 externally checkable specific (ratings, episode/season counts, dates, named plot events, production facts, figures) or a structured multi-step argument. |
| **`hot_take`** | A confident, substantive claim about TV (judgment, ranking, or factual-sounding assertion) stated **without** checkable support. |
| **`reaction`** | An expressive, social, or purely informational comment (jokes, agreement, one-liners, questions, "name a show" answers, personal anecdotes) that **doesn't argue a take at all**. |

**Real examples** (from r/television):

- `analysis` — *"HBO needed 7 seasons. GRRM said it could go to like 14 … S8 is only 6
  episodes. You could take 3 of those episodes and put them in S7 and you'd have one
  NORMAL season length."* (marshals specific episode/season counts into an argument)
- `hot_take` — *"It is wild how much love he gets when pretty much everything he does
  is trash."* (sweeping evaluative claim, zero evidence)
- `reaction` — *"i agree completely with everything you said"* (social agreement,
  no independent take)

Full definitions, two clear + one uncertain example per label, the ordered decision
rules, and the three hardest cases are documented in [`planning.md`](planning.md).

### How labels are assigned (decision procedure)

Applied in order — first match wins; this is what any second annotator gets:

1. **R1 — Is there a take?** A substantive standalone claim about a
   show/episode/performer/industry?
   - No → **`reaction`**
   - Yes → R2
2. **R2 — Is the take supported?** ≥1 externally checkable specific, or a structured
   argument that stands with the opinion words removed?
   - Yes → **`analysis`**
   - No → **`hot_take`**

Plus tiebreakers (incidental judgments → label by primary function; *length ≠
analysis*; implicit/rhetorical claims still count as takes).

---

## Data

- **Source:** [pullpush.io](https://pullpush.io) comment search for
  `subreddit=television` — a free, no-auth Pushshift-successor research archive.
  (Reddit's own API and site are bot-walled from our environment.)
- **Unit:** **comments**, not submissions — in r/television submissions are mostly
  news headlines/links, so the actual takes live in the comments.
- **Provenance snapshot:** 595 comments pulled 2026-06-21 (the raw pool is
  git-ignored because it contains usernames; the labeled CSV is the canonical,
  scrubbed artifact).

### Reproduce the data pull

```bash
python3 data/pull_reddit.py --subreddit television --pages 6 --out data/raw_comments.json
```

(The script shells out to `curl`, so it works even where Python lacks CA certs.)

---

## Repo structure

```
ai201-project3-takemeter/
├── planning.md              # working design doc + decision log (M1 complete)
├── README.md                # this file
├── data/
│   ├── pull_reddit.py       # reusable r/television comment puller (pullpush.io)
│   ├── raw_comments.json    # raw pool (git-ignored; reproducible via the script)
│   └── takemeter_dataset.csv  # ⏳ labeled dataset (M2)
├── evaluation_results.json  # ⏳ metrics from Colab (M5)
└── confusion_matrix.png     # ⏳ confusion matrix from Colab (M5)
```

## Roadmap

- **M2** — annotate ≥200 comments with the procedure above (oversampling medium/long
  comments so each label clears ~30%, since the natural mix is reaction-heavy);
  split train/val/test; document the final per-label counts and the labeling process.
- **M3** — fine-tune `distilbert-base-uncased` on Colab (T4 GPU).
- **M4** — zero-shot baseline with Groq `llama-3.3-70b-versatile` on the same test set.
- **M5** — evaluation report: overall accuracy (both models), per-class F1, confusion
  matrix, ≥3 analyzed errors, and a reflection on learned-vs-intended.
