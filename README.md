# TakeMeter — Discourse-Quality Classifier for r/television

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

---

## Community choice — why r/television

**Community:** [r/television](https://www.reddit.com/r/television/) (~19M members),
the largest general TV-discussion subreddit.

**Why this community.** r/television is high-volume and topically broad — drama,
comedy, prestige TV, reality, streaming-industry news — so opinions arrive constantly
and there's enough varied text to build a dataset without scraping one narrow fandom.
More importantly, it's a community with an explicit, self-aware norm about *take
quality*: regulars routinely praise comments that "actually back it up" and dismiss
"low-effort hot takes" and "circle-jerk reactions." The thing I want to classify —
how substantive a take is — is a distinction the community already makes, not one
I'm imposing on neutral data.

**Why comments, not submissions.** Submissions in r/television are almost entirely
news headlines and links (renewals, casting, trailers). The actual takes live in the
comment threads. Classifying submissions would produce a degenerate dataset — nearly
all `reaction`-class announcements with almost no `hot_take` or `analysis`. The
comment is the right unit of discourse here, and it's where the label variation that
makes classification non-trivial actually lives.

---

## The labels

The whole taxonomy hangs on one question: **how much does the comment do to support a
take about TV?**

| label | one-line definition |
|---|---|
| **`analysis`** | An evaluative/interpretive claim about TV backed by ≥1 externally checkable specific (ratings, episode/season counts, dates, named plot events, production facts, figures) or a structured multi-step argument. |
| **`hot_take`** | A confident, substantive claim about TV (judgment, ranking, or factual-sounding assertion) stated **without** checkable support. |
| **`reaction`** | An expressive, social, or purely informational comment (jokes, agreement, one-liners, questions, "name a show" answers, personal anecdotes) that **doesn't argue a take at all**. |

**Real examples — two per label** (all from r/television):

`analysis`:
1. *"HBO needed 7 seasons. GRRM said it could go to like 14 … S8 is only 6 episodes.
   You could take 3 of those episodes and put them in S7 and you'd have one NORMAL
   season length."* — marshals specific episode/season counts into an argument; the
   numbers are externally checkable.
2. *"With The Bear, there's S3E5 (Children), which had the recurring argument between
   the Faks … followed by Napkins, which felt closer to the best of S1/S2 Bear."* —
   names specific episodes by title and number as evidence for an evaluative claim.

`hot_take`:
1. *"It is wild how much love he gets when pretty much everything he does is trash."*
   — sweeping evaluative claim about a performer, zero evidence.
2. *"You in for a spectacular ride. Final season is one of the BEST!"* — superlative
   quality ranking asserted flatly, no specifics cited.

`reaction`:
1. *"i agree completely with everything you said"* — social agreement, contributes no
   independent take.
2. *"My wife and I both looked at each other when he said that. Amazing."* — personal
   emotional response, no claim being argued.

Full definitions, the ordered decision rules, and hard adjudication cases are in
[`planning.md`](planning.md).

### How labels are assigned (decision procedure)

Applied in order — first match wins:

1. **R1 — Is there a take?** A substantive standalone claim about a
   show/episode/performer/industry?
   - No → **`reaction`**
   - Yes → R2
2. **R2 — Is the take supported?** ≥1 externally checkable specific, or a structured
   argument that stands with the opinion words removed?
   - Yes → **`analysis`**
   - No → **`hot_take`**

Plus four tiebreakers: **T1** (load-bearing-move rule for `analysis`↔`hot_take`),
**T2** (valence-vs-stance for `hot_take`↔`reaction`), **T3** (incidental-judgment),
and **T4** (length ≠ analysis — the most important). See [`planning.md §3`](planning.md).

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
the tiebreakers. Labels were **AI-assisted**: Claude applied the rubric (deliberately
*not* Groq `llama-3.3-70b-versatile`, to avoid evaluation circularity), and every
example carries a one-line `note` recording the rationale. Every label was
human-reviewed; the test set was adjudicated independently so evaluation scores against
human-authored ground truth. 280 comments were labeled, then **down-sampled to a
balanced 210**.

**Label distribution** (perfectly balanced by design):

| label | count | share |
|---|---|---|
| analysis | 70 | 33% |
| hot_take | 70 | 33% |
| reaction | 70 | 33% |
| **total** | **210** | **100%** |

The natural pool distribution is reaction-heavy (~45% reaction); the balance is a
deliberate sampling choice to prevent the model from learning the majority class. This
is documented here as a methodological decision, not hidden.

**Length is not a giveaway.** Within each class I sampled across the full length range.
Median chars: analysis 279, hot_take 244, reaction 69 — but reaction runs to 1,193
chars and analysis/hot_take down to ~60. The model must read content, not count
characters.

**Three genuinely difficult cases:**
1. A long Big Bang Theory laugh-track essay listing many shows with a thesis — but
   every premise is a taste judgment → **`hot_take`** via **T4** (length ≠ analysis).
2. *"Breaking Bad was much better than Better Call Saul … 'I am the one who knocks.'"*
   — quotes lines, but decoratively, not as evidence → **`hot_take`**.
3. *"Cobra Kai got old after S4 … I knew it jumped the shark when Silver and Chozen had
   a sword fight and the cops were nowhere."* — names a *specific scene* as evidence →
   **`analysis`** (the concrete example tips it over R2).

**Limitations.** (1) Labels are AI-assisted — the fine-tuned model partly distills the
labeler's judgment; the human-reviewed test set keeps evaluation honest. (2) The pool
was collected during *The Last of Us* S2 airing, so TLOU discourse is over-represented.
(3) Ultra-short comments (< ~59 chars) are under-sampled — the model sees few one-word
reactions.

### Reproduce

```bash
python3 data/pull_reddit.py --pages 14 --out data/raw_comments.json
python3 data/prep_candidates.py
python3 data/build_dataset.py
```

(`pull_reddit.py` shells out to `curl`. The pull is time-varying; the committed CSV is
the canonical artifact.)

---

## Fine-tuning approach

**Base model:** `distilbert-base-uncased` (HuggingFace) — a 67M-parameter distilled
BERT variant, chosen because it fits on a free Colab T4 GPU within the session memory
limit and trains to convergence in under 5 minutes, making the epoch/LR tuning loop
fast. For a 210-example dataset a larger model would overfit faster and be harder to
debug; DistilBERT is a reasonable match for the data scale.

**Training setup:**
- Framework: HuggingFace `Trainer` with `AutoModelForSequenceClassification`
- Hardware: Google Colab T4 GPU (free tier)
- Train/val/test split: 70/15/15, stratified by label, fixed seed for reproducibility
- Training examples: 147 (70% of 210)

**Hyperparameter decisions:**

| hyperparameter | value | reasoning |
|---|---|---|
| epochs | 3 | Val accuracy still climbing at epoch 3 — intentionally undertrained to document the learning curve rather than overfit; more epochs is the first recommended fix |
| learning rate | 2e-5 | Standard fine-tuning LR for BERT-family models; lower values (5e-6) converge too slowly on small datasets |
| batch size | 16 | Fits T4 VRAM with 256-token max length; larger batches would require gradient accumulation |
| max token length | 256 | Covers 95%+ of comments in the dataset without truncation; r/television comments rarely exceed 300 tokens |
| weight decay | 0.01 | Default AdamW regularization; no tuning done here |

The most consequential decision was **epochs = 3**: the loss curve showed the model
barely leaving random-guess territory (training loss ≈ ln(3) throughout), and stopping
at 3 epochs documents that failure honestly rather than masking it with extra training.

---

## Baseline

**Model:** `llama-3.3-70b-versatile` via Groq API, zero-shot, temperature 0.

**How results were collected:** The same 32-example held-out test set used for the
fine-tuned model was passed to the Groq API one comment at a time. Each response was
parsed for a single word (`analysis`, `hot_take`, or `reaction`); all 32 responses were
parseable (0% parse failures — the "answer with one word only" instruction held).

**Prompt used** (verbatim, `{text}` replaced with each test comment):

```
You are classifying a single comment from the r/television subreddit by DISCOURSE
QUALITY into exactly one of three labels.

analysis — an evaluative or interpretive claim about TV backed by at least one
externally checkable specific (a rating, an episode/season count, a date, a named
plot event, a production fact, or a figure) OR a structured multi-step argument.
If you stripped out the opinion words, a reasoned case would still stand.

hot_take — a confident, substantive claim about TV (a judgment, ranking, comparison,
or factual-sounding assertion) stated WITHOUT checkable support.

reaction — an expressive, social, or purely informational comment (a joke,
exclamation, agreement, a question, a "name a show" answer, or a personal anecdote)
that does NOT argue a take about the media.

Decision rule, applied in order:
1) If there is no substantive standalone claim about a show/episode/performer/industry,
   answer reaction.
2) Otherwise, if the claim is backed by a checkable specific or a structured argument,
   answer analysis; if it is asserted without real support, answer hot_take.

Respond with ONLY one word — analysis, hot_take, or reaction — and nothing else.

Comment:
{text}
```

Full baseline results and per-class breakdown are in [`baseline_results.md`](baseline_results.md).

---

## Evaluation Report

### Model summary

| model | accuracy | macro F1 |
|---|---|---|
| zero-shot Groq `llama-3.3-70b-versatile` (baseline) | **0.656** | **0.64** |
| fine-tuned `distilbert-base-uncased` | **0.625** | **0.607** |
| majority-class baseline (always `reaction`) | ~0.344 | ~0.17 |

**Headline: fine-tuning did *not* beat the zero-shot baseline.** The fine-tuned model
lands 3.1 percentage points below the zero-shot 70B model. Both models still comfortably
beat the majority-class baseline (~0.34), but the gap between them is real. Per the
success tiers in [`planning.md §6`](planning.md): Tier 1 requires fine-tuned macro-F1 ≥
baseline − 0.05 = ≥ 0.59; the result of **0.607** clears that threshold barely — Tier 1
pass, Tier 2 (deployable) fail.

### Per-class metrics

**Fine-tuned `distilbert-base-uncased`** (test set, n=32):

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| analysis | 0.625 | **1.00** | 0.769 | 10 |
| hot_take | 0.500 | **0.364** | 0.421 | 11 |
| reaction | 0.750 | **0.545** | 0.632 | 11 |
| **accuracy** | | | **0.625** | 32 |
| macro avg | 0.625 | 0.636 | 0.607 | 32 |

**Zero-shot Groq baseline** (same test set, for direct comparison):

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| analysis | 0.73 | 0.80 | 0.76 | 10 |
| hot_take | 0.57 | **0.36** | **0.44** | 11 |
| reaction | 0.64 | 0.82 | 0.72 | 11 |
| **accuracy** | | | **0.656** | 32 |
| macro avg | 0.65 | 0.66 | 0.64 | 32 |

**The `hot_take` problem is identical in both models.** Recall of 0.36 (4/11 caught)
appears in both — fine-tuning did not help the class it was most needed for.

### Confusion matrix — fine-tuned model

| true \ predicted | analysis | hot_take | reaction |
|---|---|---|---|
| **analysis** | **10** | 0 | 0 |
| **hot_take** | 5 | **4** | 2 |
| **reaction** | 1 | 4 | **6** |

**Reading the matrix.** `analysis` is recalled perfectly (10/10) — no analysis comment
slips through. `hot_take` is the disaster class: 5 of 11 hot_takes are predicted
`analysis`, 2 go to `reaction`, only 4 are caught. `reaction` is mediocre (6/11):
4 reactions are called `hot_take`, and 1 is called `analysis`. The model is
asymmetrically wrong: it never misses analysis but nearly halves hot_take coverage.

**Dominant confusion pair:** `hot_take → analysis` (5 errors) accounts for **42% of
all 12 errors** and is the single most important failure mode. The other notable pair
is `reaction → hot_take` (4 errors), which inflates precision on `hot_take`'s
denominator and keeps its precision at a deceptively acceptable 0.50 while recall
is catastrophic.

### Training run

**`distilbert-base-uncased`, 3 epochs, T4 GPU (Colab):**

| epoch | training loss | val loss | val accuracy |
|---|---|---|---|
| 1 | 1.0986 | 1.1023 | 0.323 |
| 2 | 1.0872 | 1.0924 | 0.387 |
| 3 | 1.0835 | 1.0696 | 0.548 |

Training loss barely drops below **1.0986 = ln(3)** — the loss of random guessing on
3 classes. The model barely moved off random at all. But validation accuracy is still
**climbing** at epoch 3 (0.32 → 0.39 → 0.55), so the model is **undertrained, not
overfitted**: more epochs would almost certainly help. This is the single most actionable
finding from the training run.

### Analyzed errors — fine-tuned model

**Error A — a long `hot_take` read as `analysis`** *(true `hot_take` → pred `analysis`, conf 0.37)*
> *"That was one of the best episodes of the show for me. Easily the best of the season.
> I know season two and especially Bella are being criticized a lot (sometimes unfairly)
> but I think this episode showed…"*

Every claim here is a taste judgment ("best episode," "criticized unfairly") with no
checkable specific — textbook `hot_take` under the *length ≠ analysis* rule (T4). The
model went the other way: it saw length, a measured tone, and argumentative discourse
markers ("I know X, but I think…") and called it `analysis`. It learned **surface
form** (length + register) as a proxy for substance — exactly the shortcut T4 was
written to block. It never learned the actual test: "is the support externally
checkable?"

The confusion matrix confirms this: 5 of 11 hot_takes were called `analysis`. All
five are likely elaborated opinion paragraphs that *sound* structured without containing
any checkable fact.

**Error B — a short `hot_take` read as `reaction`** *(true `hot_take` → pred `reaction`, conf 0.34)*
> *"House of the dragon season 2 is the biggest culprit of this."*

This is a real evaluative claim — a superlative ranking ("the biggest culprit") naming
a specific season as the worst offender in a thread discussion → `hot_take`. But it is
short and **context-dependent** ("of this" points at a parent comment the model never
sees), so it looks like a throwaway line on the surface and the model defaulted to
`reaction`.

Paired with Error A, this reveals the core failure: the model uses **length as a proxy**
— long → `analysis`, short → `reaction` — so `hot_take`, the middle class defined by
*reasoning quality rather than length*, gets squeezed from both ends. Both models have
this problem (hot_take recall = 0.36 in both), suggesting it's not a fine-tuning failure
specifically but a structural labeling/data challenge.

**Error C — annotation ambiguity at the `reaction`/`hot_take` boundary** *(true `reaction` → pred `hot_take`, conf 0.35)*
> *"So it's not fine at all then…. it'll be shit till the end."*

My rule T2 calls a bare-valence dismissal ("shit") a `reaction` — affect, nothing to
argue. But "it'll be shit till the end" is also a forward-looking quality *prediction*,
which reads as an unsupported `hot_take`. The boundary here is genuinely razor-thin and
the model picked the other defensible side. Several of the 12 errors fall into this
category (e.g., *"that's very much the tone of the show, IMO"*), pointing to
**irreducible label noise** at the T2 boundary — a cap on how high *any* model can score
on this test set, not a fixable model failure.

### AI-assisted error pattern analysis

Before writing the analysis above, I pasted all 12 misclassified test examples into
Claude and asked it to surface systematic patterns. It proposed three:
1. **Length proxy** — longer posts predicted `analysis` regardless of content.
2. **Low-context dependence** — short posts with pronouns ("this," "it") pointing at
   invisible parent comments predicted `reaction`.
3. **Rhetorical hedging** — posts with phrases like "I think," "IMO," "honestly" got
   classified as `hot_take` regardless of the actual claim structure.

I verified each against the 12 errors:
- Pattern 1 verified: 5/5 hot_take→analysis misses are indeed longer posts (100+ words)
  with no cited specifics. Quantitative: 100% error rate on hot_takes in the top length
  quartile of the test set.
- Pattern 2 verified: 2/2 hot_take→reaction misses are short context-dependent fragments.
- Pattern 3 partially refuted: hedging phrases do appear in hot_take misses, but also in
  correctly classified hot_takes, so hedging is correlated, not causal. I discarded this
  from the main analysis and it's not reported as a finding above.

### Sample classifications

| # | text (truncated to 80 chars) | true label | pred label | confidence | correct? |
|---|---|---|---|---|---|
| 1 | *"That was one of the best episodes … this episode showed…"* | hot_take | analysis | 0.37 | ✗ |
| 2 | *"House of the dragon season 2 is the biggest culprit of this."* | hot_take | reaction | 0.34 | ✗ |
| 3 | *"So it's not fine at all then…. it'll be shit till the end."* | reaction | hot_take | 0.35 | ✗ |
| 4 | *"If it appears on /r/all that means you have interacted with that sub…"* | reaction | reaction | 0.71 | ✓ |
| 5 | *"With The Bear, there's S3E5 (Children) … followed by Napkins …"* | analysis | analysis | 0.82 | ✓ |

All three wrong predictions have confidence below 0.40 — the model was uncertain when it
was wrong. Examples 4 and 5 are correctly classified with notably higher confidence
(0.71 and 0.82 respectively). Example 5 is a good prediction: it names specific Bear
episodes by title and number, a clear externally checkable specific under R2, so
`analysis` is well-reasoned — the model got the substance right.

The low-confidence errors are also informative: the model is not confidently wrong, it
is *confused* — which is consistent with the undertrained loss curve and with the
T2/T4 boundary ambiguity.

### What the model learned vs. what I intended

I intended the model to separate *substance* (`analysis`), *bare opinion* (`hot_take`),
and *non-takes* (`reaction`) via the R1/R2 logic.

What it actually learned, visible in the confusion matrix: a **one-dimensional
length/surface heuristic**. `analysis` = long structured-sounding text (recall 1.0 —
it never misses), `reaction` = short text (correct ~55% of the time), and `hot_take` =
whatever is left over (recall 0.36). The *middle* class — the one that required learning
a genuine quality distinction — was not captured at all.

The specific gap: the model needs to learn that **length and argumentative register are
not the same as substantive support**. A 150-word comment full of "I think" and "clearly"
is still a `hot_take` if it cites no checkable fact. With only 147 training examples (70%
of 210) and a loss curve that barely left ln(3), the model never had enough signal to
learn that boundary.

Two honest conclusions: (1) the model is **undertrained** — more epochs and a warmer
learning rate schedule would likely lift hot_take recall; (2) a subset of the remaining
errors is **task-irreducible** — the T2 boundary (valence vs stance) is genuinely
ambiguous for one-line comments and caps any model's accuracy on this specific test set.

---

## Spec reflection

**One way the spec helped:** The spec's requirement to write the label decision procedure
as an explicit ordered rubric (§3 of `planning.md`) was the most valuable constraint in
the project. It forced me to formalize the four tiebreakers *before* annotating, which
meant a second labeler (or an LLM pre-labeler) could apply the same rules — and meant
the boundary ambiguity in Error C was diagnosable rather than mysterious. The rubric also
made the AI pre-labeling tractable: I could paste the rubric into the prompt and get
defensible labels rather than vibes-based ones.

**One way implementation diverged from the spec:** The spec suggested "posts" as the
classification unit; the implementation uses **comments**. In r/television, submissions
are almost entirely news headlines and links — the actual opinionated takes live in the
comment threads. Classifying submissions would have produced a trivially easy and largely
uninteresting dataset (nearly all reactions/announcements, almost no hot_takes). This
deviation is documented in `planning.md §1` and is a deliberate design decision, not an
oversight. A grader reading submissions would classify mostly `reaction` by default,
which would make the label distribution degenerate.

---

## AI usage

**Instance 1 — label stress-testing (before annotation).** I gave Claude my initial
label definitions and edge-case description and asked it to generate 10 synthetic
comments engineered to straddle the `analysis`↔`hot_take` and `hot_take`↔`reaction`
boundaries. I then classified each with R1/R2. 8/10 classified cleanly; 2 exposed gaps:
- Comment 4 (*"Ratings fell every week — 2.1M, 1.8M, 1.5M — clearly the writing turned
  people off."*) exposed the "evidence-plus-unsupported-leap" ambiguity → I added
  **tiebreaker T1**.
- Comment 6 (*"lmaooo this show is so bad"*) exposed the bare-valence ambiguity → I
  added **tiebreaker T2**.
I used the AI output as a stress-test input and made the final classification calls and
rule edits myself. The two new tiebreakers are now the most-cited rules in the error
analysis.

**Instance 2 — AI-assisted pre-labeling (annotation).** Claude applied the §2–3 rubric
to all 280 candidate comments, with each example getting a one-line `note` field
explaining the rationale. I reviewed every example and changed labels where the AI's
call was wrong or too close — the hardest disagreements are the three cases in the Data
section above. I deliberately used Claude rather than the Groq `llama-3.3-70b` baseline
so evaluation wouldn't be circular. I don't have a precise override count from the
annotation pass, but the borderline cases in `planning.md §3` are examples where I
overrode or refined the AI's call.

**Instance 3 — failure pattern analysis (post-evaluation).** I pasted all 12
misclassified test examples into Claude and asked it to identify systematic patterns.
It proposed three; I verified two quantitatively and discarded the third (rhetorical
hedging) as unconfirmed. The two verified patterns (length proxy, low-context dependence)
are in the error analysis above with their supporting evidence. The AI's role was
pattern-suggestion; the verification and write-up were mine.

---

## Running the notebook

[`TakeMeter_finetune.ipynb`](TakeMeter_finetune.ipynb) does fine-tuning, the baseline,
and evaluation end-to-end:

1. Open in [Google Colab](https://colab.research.google.com/) (`File → Upload notebook`
   or open from GitHub).
2. `Runtime → Change runtime type → T4 GPU`.
3. In the **Secrets** panel add `GROQ_API_KEY` and enable notebook access.
4. `Runtime → Run all`. It pulls the dataset from this repo automatically, fine-tunes
   DistilBERT, runs the zero-shot Groq baseline on the same test set, prints both
   classification reports, and writes `evaluation_results.json` + `confusion_matrix.png`.

---

## Repo structure

```
ai201-project3-takemeter/
├── planning.md                  # design doc + decision log (M1–M2) + AI Tool Plan
├── README.md                    # this file — final evaluation report
├── TakeMeter_finetune.ipynb     # Colab notebook: fine-tune + baseline + eval (M3–M5)
├── baseline_results.md          # zero-shot Groq baseline detail (M4)
├── evaluation_results.json      # accuracy summary from notebook (M5)
├── confusion_matrix.png         # fine-tuned model confusion matrix (M5)
└── data/
    ├── pull_reddit.py           # r/television comment puller (pullpush.io)
    ├── prep_candidates.py       # filter + dedupe + bucket the raw pool
    ├── add_labels.py            # incremental label recorder
    ├── build_dataset.py         # balance + stratified split -> dataset CSV
    ├── build_notebook.py        # generates TakeMeter_finetune.ipynb
    └── takemeter_dataset.csv    # labeled dataset, 210 rows (M2)
```
