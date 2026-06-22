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
| M4 | Zero-shot baseline (`llama-3.3-70b-versatile` via Groq) | ✅ done — acc **0.656**, see [`baseline_results.md`](baseline_results.md) |
| M3 | Fine-tune `distilbert-base-uncased` (Colab T4) | ▶️ next — starter notebook, same test split as the baseline |
| M5 | Evaluation report (accuracy, per-class F1, confusion matrix, error analysis) | ⏳ pending — compare fine-tuned vs the 0.656 baseline |

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
Per the AI Tool Plan, these pre-labels should be **reviewed by you** before training (the
notebook chooses the test split, so review especially weighs there). 280 comments were
labeled in total, then **down-sampled to a balanced 210** (the natural mix is
reaction-heavy, so this is a deliberate sampling choice — see *Limitations*).

**Label distribution** (perfectly balanced by design — max label share 33%, well under
the 70% imbalance threshold). The CSV is a **single, un-split** file (`text`, `label`,
`note`); the notebook does the 70/15/15 train/val/test split automatically.

| label | count | share |
|---|---|---|
| analysis | 70 | 33% |
| hot_take | 70 | 33% |
| reaction | 70 | 33% |
| **total** | **210** | **100%** |

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

## Evaluation

**Headline: fine-tuning did *not* beat the zero-shot baseline.** The fine-tuned
DistilBERT scored **0.625** on the 32-example test set (12/32 wrong) vs the zero-shot
Groq baseline's **0.656** ([`baseline_results.md`](baseline_results.md)).

**Training run** (`distilbert-base-uncased`, 3 epochs):

| epoch | training loss | validation loss | val accuracy |
|---|---|---|---|
| 1 | 1.0986 | 1.1023 | 0.323 |
| 2 | 1.0872 | 1.0924 | 0.387 |
| 3 | 1.0835 | 1.0696 | 0.548 |

The training loss barely drops below **1.0986 = ln(3)**, the loss of random guessing on
3 classes — the model hardly learned. But validation loss falls monotonically and val
accuracy is *still climbing* at epoch 3 (0.32 → 0.39 → 0.55), so the model is
**under-trained, not over-fit**: more epochs is the first thing to try.

### Three wrong predictions, analyzed

**A — a long `hot_take` read as `analysis`** *(true `hot_take` → pred `analysis`, conf 0.37)*
> *"That was one of the best episodes of the show for me. Easily the best of the season. I know season two and especially Bella are being criticized a lot (sometimes unfairly) but I think this episode showed…"*

Every claim here is a taste judgment ("best episode," "criticized unfairly") with no
checkable specific — a textbook `hot_take` under the *length ≠ analysis* rule (T4). The
model went the other way: it saw length, a measured tone, and the discourse markers of
argument ("I know X, but I think…") and called it `analysis`. It learned **surface form**
(length + argumentative register) as a proxy for substance — exactly the shortcut T4 was
written to block. It never learned the actual test ("is the support externally checkable?").

**B — a short `hot_take` read as `reaction`** *(true `hot_take` → pred `reaction`, conf 0.34)*
> *"House of the dragon season 2 is the biggest culprit of this."*

This is a real evaluative claim — a superlative ranking ("the biggest culprit") naming a
season as the worst offender of whatever the thread is discussing → `hot_take`. But it's
short and **context-dependent** ("of this" points at a parent comment the model never
sees), so on the surface it looks like a throwaway line, and the model defaulted to
`reaction`. Paired with **A**, this is the core pattern: the model uses **length as a
proxy** — long → analysis, short → reaction — so `hot_take`, the *middle* class defined by
reasoning quality rather than length, gets squeezed out from both ends. (Same failure as
the baseline: `hot_take` recall stuck at **0.36** in *both* models.)

**C — annotation ambiguity, `reaction` vs `hot_take`** *(true `reaction` → pred `hot_take`, conf 0.35)*
> *"So it's not fine at all then…. it'll be shit till the end."*

Here the model's "error" is defensible. My rule T2 calls a *bare-valence* dismissal
("shit") a `reaction` — affect, nothing to argue. But "it'll be shit till the end" is also
a forward-looking quality *prediction*, which reads as an unsupported `hot_take`. The
boundary is razor-thin and the model picked the other reasonable side. Several of the 12
errors are like this (e.g. #12, *"that's very much the tone of the show, IMO"*), so part of
the error rate is **irreducible label noise**, not model failure — and it means my own T2
calls on these one-liners cap how high *any* model can score on this test set.

### What the model learned vs. what I intended

I intended the model to separate *substance* (`analysis`), *bare opinion* (`hot_take`),
and *non-takes* (`reaction`) via the R1/R2 logic. With only 147 training examples and a
near-flat loss curve, it instead learned a weak **length/surface heuristic** and never
captured the `hot_take` middle — the very distinction this project is about. My M4
hypothesis (fine-tuning would lift `hot_take` recall from 0.36 toward ≥0.60) was
**falsified**: it stayed at 0.36. Two honest takeaways: the model is *undertrained* (try
more epochs), and some labels are genuinely ambiguous (**C**), so a chunk of the gap is
task subjectivity, not model capacity.

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
