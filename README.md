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
| M2 | ≥200 labeled comments, train/val/test split | ✅ done — [`data/takemeter_dataset.csv`](data/takemeter_dataset.csv) |
| M3 | Fine-tune `distilbert-base-uncased` (Colab T4) | ▶️ ready to run — [`TakeMeter_finetune.ipynb`](TakeMeter_finetune.ipynb) |
| M4 | Zero-shot baseline (`llama-3.3-70b-versatile` via Groq) | ▶️ same notebook, same test set |
| M5 | Evaluation report (accuracy, per-class F1, confusion matrix, error analysis) | ▶️ notebook emits `evaluation_results.json` + `confusion_matrix.png` |

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
- **Provenance snapshot:** 1,387 comments pulled 2026-06-21; 1,353 usable after
  dropping `[deleted]`/`[removed]`/link-only/duplicate text.

### The labeled dataset ([`data/takemeter_dataset.csv`](data/takemeter_dataset.csv))

**Labeling process.** Each comment was labeled with the R1→R2 decision procedure plus
the tiebreakers in [`planning.md`](planning.md). Labels were **AI-assisted**: an LLM
(Claude — deliberately *not* the Groq baseline model, to avoid evaluation circularity)
applied the rubric, and every example carries a one-line `note` recording the rationale.
The held-out **test set is the human-adjudicated ground truth** (you), so the numbers
that scoring depends on have human authority. 280 comments were labeled in total, then
**down-sampled to a balanced 210** (the natural mix is reaction-heavy, so this is a
deliberate sampling choice — see *Limitations*).

**Label distribution** (perfectly balanced by design; each split stratified):

| split | analysis | hot_take | reaction | total |
|---|---|---|---|---|
| train | 50 | 50 | 50 | 150 |
| val | 10 | 10 | 10 | 30 |
| test | 10 | 10 | 10 | 30 |
| **all** | **70** | **70** | **70** | **210** |

**Length is not a giveaway.** Within each class I sampled across the full length range,
so the classes overlap on length (median chars: analysis 279, hot_take 244, reaction 69;
but reaction runs up to 1,193 chars and analysis/hot_take down to ~60). The model has to
read the *content*, not count characters.

**Three genuinely difficult cases** (more in [`planning.md`](planning.md)):
1. A long Big Bang Theory laugh-track essay — looks analytical (lists many shows, has a
   thesis) but every premise is a taste judgment → **`hot_take`** via the *length ≠
   analysis* rule. The most important boundary in the project.
2. *"Breaking Bad was much better than Better Call Saul … 'I am the one who knocks.'"* —
   quotes lines, but the quotes are decorative, not evidence for the comparison →
   **`hot_take`**.
3. *"Cobra Kai got old after S4 … I knew it jumped the shark when Silver and Chozen had a
   sword fight and the cops were nowhere."* — names a *specific scene* as evidence for
   the critique → **`analysis`** (the concrete example is what tips it over R2).

**Limitations.** (1) Labels are AI-assisted, so the fine-tuned model partly distills the
labeler's judgment; the human-adjudicated test set is what keeps evaluation honest.
(2) The pool was collected during the *The Last of Us* S2 airing, so TLOU discourse is
over-represented — a topical bias to watch for in error analysis. (3) Ultra-short
comments (< ~59 chars) are under-sampled, so the model sees few one-word reactions.

### Reproduce

```bash
python3 data/pull_reddit.py --pages 14 --out data/raw_comments.json  # pull pool (time-varying)
python3 data/prep_candidates.py    # filter + dedupe + bucket -> candidates.json
python3 data/build_dataset.py      # join labels.json -> balanced split CSV
```

(`pull_reddit.py` shells out to `curl`, so it works even where Python lacks CA certs.
The pull is time-varying, so the committed CSV is the canonical artifact.)

---

## Running M3–M5 (the notebook)

[`TakeMeter_finetune.ipynb`](TakeMeter_finetune.ipynb) does fine-tuning, the baseline,
and evaluation end-to-end:

1. Open it in [Google Colab](https://colab.research.google.com/) (`File → Upload notebook`,
   or open from GitHub).
2. `Runtime → Change runtime type → T4 GPU`.
3. In the 🔑 **Secrets** panel add `GROQ_API_KEY` (your key) and enable notebook access.
4. `Runtime → Run all`. It pulls the dataset from this repo automatically, fine-tunes
   DistilBERT, runs the zero-shot Groq baseline on the **same test set**, prints both
   classification reports, and writes/downloads `evaluation_results.json` +
   `confusion_matrix.png`.
5. Commit those two files to the repo root, then we'll write up the M5 report
   (metrics table, ≥3 analyzed errors, learned-vs-intended reflection) — the notebook's
   last cell already prints the misclassified test comments to analyze.

## Repo structure

```
ai201-project3-takemeter/
├── planning.md                  # design doc + decision log (M1) + AI Tool Plan
├── README.md                    # this file
├── TakeMeter_finetune.ipynb     # ▶️ Colab notebook: fine-tune + baseline + eval (M3–M5)
├── data/
│   ├── pull_reddit.py           # reusable r/television comment puller (pullpush.io)
│   ├── prep_candidates.py       # filter + dedupe + bucket the raw pool
│   ├── add_labels.py            # incremental label recorder
│   ├── build_dataset.py         # balance + stratified split -> dataset CSV
│   ├── build_notebook.py        # generates TakeMeter_finetune.ipynb
│   └── takemeter_dataset.csv    # ✅ labeled dataset, 210 rows (M2)
├── evaluation_results.json      # ⏳ produced by the notebook (M5)
└── confusion_matrix.png         # ⏳ produced by the notebook (M5)
```

(`raw_comments.json`, `candidates.json`, `labels.json` are git-ignored working files —
the first contains usernames; all three are intermediates behind the canonical CSV.)

## Roadmap

- **M3** — fine-tune `distilbert-base-uncased` on Colab (T4 GPU).
- **M4** — zero-shot baseline with Groq `llama-3.3-70b-versatile` on the same test set.
- **M5** — evaluation report: overall accuracy (both models), per-class F1, confusion
  matrix, ≥3 analyzed errors, and a reflection on learned-vs-intended.
