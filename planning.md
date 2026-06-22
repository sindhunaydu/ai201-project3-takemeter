# TakeMeter — Planning

**TakeMeter** is a fine-tuned text classifier that scores *discourse quality* in
[r/television](https://www.reddit.com/r/television/): given a comment, it predicts how
much the comment actually **argues** a take about TV — `analysis`, `hot_take`, or
`reaction`.

This document is organized around the six planning questions for the project, followed
by an **AI Tool Plan** and a data-provenance appendix. The labels and their decision
rules (§2–3) are the load-bearing part — everything downstream depends on them — so
they get the most space, and I stress-tested them with an LLM (§7) *before* writing this
plan, which is why the rules in §3 are already tightened.

---

## 1. Community — why r/television

**Choice:** r/television (~19M members), the largest general TV-discussion subreddit.

**Why this community.** It's high-volume and topically broad (drama, comedy, prestige TV,
reality, streaming-industry news), so opinions arrive constantly and there's enough
fresh text to build a dataset without scraping one narrow fandom. It's also a community
with an explicit, self-aware norm about *take quality*: regulars routinely praise
comments that "actually back it up" and dismiss "low-effort hot takes" and "circle-jerk"
reactions. So the thing I want to classify — how substantive a take is — is a distinction
the community already polices, not one I'm imposing.

**Why it's a good fit for classification (the discourse is genuinely varied).** Reading a
sample of real comments (see §4), the *same thread* produces wildly different registers:
a one-word joke, a flat "this show is trash," and a 200-word argument citing episode
ratings can all sit under one post. That spread is exactly what makes the task non-trivial
and worth modeling — if every comment looked the same, there'd be nothing to learn. The
variation is structured (it tracks how much evidence/reasoning a comment carries), which
is what lets it become labels rather than noise.

**Unit of classification = the comment, not the submission.** In r/television, submissions
are overwhelmingly *news headlines and links* (renewals, casting, trailers). The actual
takes live in the **comments**, so the comment is the unit. (This is a deliberate
deviation from the brief's wording of "posts"; documented here and in the README.)

---

## 2. Labels

The taxonomy hangs on one question: **how much does the comment do to support a take
about TV?** More support → `analysis`; a bare take → `hot_take`; no take at all →
`reaction`. This is a quality gradient, which is what "discourse quality" means here.

| label | one-sentence definition |
|---|---|
| **`analysis`** | An evaluative or interpretive claim about TV that is backed by at least one externally checkable specific (a rating, an episode/season count, a date, a named plot event, a production fact, a figure) or by a structured multi-step argument that would still stand if the opinion words were removed. |
| **`hot_take`** | A confident, substantive claim about TV — a judgment, ranking, comparison, or factual-sounding assertion — that is stated without any checkable support. |
| **`reaction`** | An expressive, social, or purely informational comment — a joke, an exclamation, agreement/disagreement, a question, a "name a show" answer, or a personal anecdote — that does not advance an arguable take about the media at all. |

### Two example comments per label (all real, from r/television)

**`analysis`**
1. *"HBO needed 7 seasons. GRRM said it could go to like 14. HBO thought 10. They gave 8 …
   S8 is only 6 episodes. You could take 3 of those episodes and put them in S7 and you'd
   have one NORMAL season length."* — specific episode/season counts marshalled into an argument.
2. *"They top this in S10, there's a terrible Carol & Daryl filler episode with a deserved
   4.1 rating which is immediately followed by Negan's backstory with a 9.2 rating …"* —
   cites specific episode ratings as evidence.

**`hot_take`**
1. *"It is wild how much love he gets when pretty much everything he does is trash."*
   (on Tom Hardy) — sweeping evaluative claim, zero evidence.
2. *"Way too far down. It's easily my favourite terrible person show."* — a ranking
   judgment asserted flatly.

**`reaction`**
1. *"BEES?!"* — pure exclamation/reference, no claim.
2. *"i agree completely with everything you said"* — social agreement, contributes no
   independent take.

### Decision procedure (this is what makes the labels mutually exclusive)

Apply in order; first match wins. This is the exact rubric handed to any second annotator.

- **R1 — Is there a take?** Does the comment make a substantive, *arguable* standalone
  claim about a show/episode/performer/industry?
  - **No** → `reaction`.
  - **Yes** → go to R2.
- **R2 — Is the take supported?** Is it backed by ≥1 externally checkable specific, or a
  structured argument that survives stripping the opinion words?
  - **Yes** → `analysis`.
  - **No** → `hot_take`.

---

## 3. Hard edge cases & how I'll handle them

Genuinely ambiguous comments aren't a flaw in the taxonomy — they're where the boundary
needs an explicit rule. The two boundaries that produce ambiguity are
**`analysis`↔`hot_take`** (is the support real?) and **`hot_take`↔`reaction`** (is there a
take at all?). My LLM stress-test (§7) hit exactly these two, and each produced a
tiebreaker:

- **T1 — Load-bearing-move rule (`analysis`↔`hot_take`).** When a comment mixes real
  evidence with an unsupported leap, label by what carries the *main* claim. If the
  checkable evidence supports the headline claim → `analysis`; if the evidence is
  incidental/decorative and the headline claim rests on the leap → `hot_take`.
  *Example:* *"Ratings fell every week — 2.1M, 1.8M, 1.5M — clearly the writing turned
  people off."* The numbers prove viewership dropped but say nothing about **why**; the
  actual claim ("writing turned people off") is unsupported → `hot_take`.
- **T2 — Valence-vs-stance rule (`hot_take`↔`reaction`).** A bare expression of sentiment
  ("so bad," "amazing," "trash," "mid," "🔥," "loved it") is `reaction` — it's affect with
  nothing to argue. A *specific, arguable evaluative stance* is `hot_take` even when short:
  superlatives/rankings ("worst finale ever"), comparisons ("better than X"), or named
  attributions ("overrated," "miscast," "derivative," "lazy writing"). So *"lmaooo this
  show is so bad"* → `reaction`; *"Overrated."* → `hot_take`.
- **T3 — Incidental-judgment rule.** If an evaluative aside sits inside an otherwise
  expressive/personal comment, label by the comment's *primary function* (the judgment must
  be the point to count as `hot_take`). *Example:* *"funny how the TV show made me appreciate
  the awful part 2 a bit more"* → `reaction`; "awful" is an aside, the point is a personal
  experience.
- **T4 — Length ≠ analysis.** A long comment whose load-bearing claims are *all* unsupported
  taste judgments is an elaborated opinion, not analysis. (This is the most important rule —
  it stops the model from learning "long = good take.")

**Three real cases I had to adjudicate** (full reasoning carried from M1):
1. A long Big Bang Theory laugh-track essay that lists many shows and has a thesis but whose
   every premise is itself a taste judgment → `hot_take` via **T4**.
2. *"Nailed it. One of the few perfect TV finales."* → `hot_take`, not `reaction`: the second
   clause is a standalone ranking claim (R1 yes), unsupported (R2 no).
3. *"The episodes without him have been mediocre at best, there aren't any strong actor to
   compensate his loss."* → `hot_take`: it offers a *reason*, but the reason is itself
   unsupported assertion (R2 fails).

**Handling during annotation.** I will (a) apply R1→R2→tiebreakers to every comment; (b) keep
a free-text `notes` column and a `borderline` flag on any case that wasn't obvious; (c) if a
*new* recurring borderline pattern emerges that the four tiebreakers don't cover, write a new
rule and **re-scan all already-labeled examples** for consistency before continuing; and (d)
treat the human (you) as the final adjudicator on the **test set** specifically, so the
ground truth used for scoring has human authority (see §7).

---

## 4. Data collection plan

- **Where.** [pullpush.io](https://pullpush.io) — a free, no-auth Pushshift-successor archive
  of Reddit. (Reddit's own API and site are bot-walled from this environment; pullpush is the
  working source.) Endpoint: `…/reddit/search/comment/?subreddit=television`. Puller:
  [`data/pull_reddit.py`](data/pull_reddit.py).
- **How many.** Target **≥240 labeled comments** so that after dropping junk
  (`[deleted]`/`[removed]`/link-only/empty) I safely clear the **200** floor. Target
  distribution **~33% per label, with a hard floor of ~30% (≈72 each)** — comfortably above
  the brief's 20% minimum and well clear of the 80% danger zone.
- **The balancing problem and the fix.** The *natural* distribution is reaction-heavy
  (~45/30/25 in a 20-comment validation sample). Left alone, the model would over-learn
  `reaction`. Fix: pull a large pool (~1,000 comments), bucket by character length, and
  **oversample medium (70–320 chars) and long (≥320) comments**, which is where `analysis`
  and `hot_take` concentrate, until each label hits its target count. I'll document the final
  per-label counts and explicitly flag this as a deliberate sampling bias in the README.
- **If a label is still underrepresented after 200.** Targeted re-pulls rather than settling:
  - `analysis` short → re-query and keep only longer comments, or filter the pool for comments
    containing digits / "S\d"/"episode"/"rating" (proxies for evidence-bearing comments).
  - `hot_take` short → mine ranking/"unpopular opinion"/"overrated" threads, which are dense
    with unsupported judgments.
  - As a last resort, relax the floor to ~25% (still > the 20% requirement) and **document the
    final imbalance and its expected effect on recall** rather than hiding it.
- **Splits.** Stratified **train/val/test = 70/15/15**, preserving per-label proportions in
  each split, fixed RNG seed for reproducibility. Dedupe by Reddit comment `id` and verify no
  comment appears in two splits (leakage check) — a leak would inflate test accuracy and is the
  first thing I'll suspect if results look suspiciously high (>~0.90 on this subjective task).

---

## 5. Evaluation metrics

I'll evaluate **both** the fine-tuned DistilBERT and the zero-shot Groq baseline on the **same
held-out test set**, reporting:

| metric | why it's needed here |
|---|---|
| **Overall accuracy** | Headline number and the basis for the baseline comparison — but **insufficient alone**: the classes are imbalanced, so a model that always predicts `reaction` scores ~0.42 while learning nothing. Accuracy can look "okay" while a whole class is ignored. |
| **Macro-averaged F1** *(primary metric)* | Averages F1 across the three classes with **equal weight regardless of class size**, so competence on the minority classes (`analysis`, `hot_take`) actually counts. This is the right headline for an imbalanced, subjective task. |
| **Per-class precision / recall / F1** | Locates *where* the model works. Two are deployment-critical: **`analysis` precision** (does it avoid falsely elevating junk to "good take"?) and **per-class recall** (is any class being collapsed?). |
| **Confusion matrix** | Shows *which pairs* get confused. I expect `hot_take`↔`analysis` (the support boundary) and `hot_take`↔`reaction` (short judgments). If most errors are `analysis`↔`reaction` instead, the model likely learned a proxy like length rather than the real boundary — the matrix is how I'd catch that. |
| **Baseline delta** | Fine-tuned minus zero-shot on every metric above — the only honest way to answer "did fine-tuning actually help, and by how much?" |
| *(stretch)* **Confidence calibration** | Whether a 0.9-confidence prediction is right more often than a 0.6 one — matters if the deployed tool ever thresholds on confidence. |

**Why this set for *this* task specifically:** the task is subjective and imbalanced, and the
*interesting* signal lives in the minority classes (especially `analysis`). Accuracy rewards
predicting the majority; macro-F1 + per-class metrics + the confusion matrix are what expose
minority-class failure and proxy-learning, which a single accuracy number would hide.

---

## 6. Definition of success

Success is tiered and stated as **specific numbers on the held-out test set** so it can be
judged objectively at the end.

**Realistic ceiling.** This is a subjective task; the practical ceiling is human–human
agreement, which I estimate around **~80% / Cohen's κ ≈ 0.65** (I'll measure it if I do the
inter-annotator stretch). A model can't be expected to beat that, and >~0.95 accuracy would be
a red flag for leakage or trivially easy labels, not a triumph.

**Tier 1 — "the model learned something" (assignment-level success):**
- Fine-tuned **accuracy ≥ 0.60** *and* **macro-F1 ≥ 0.60** (decisively beats the ~0.42 majority
  baseline and ~0.33 random).
- **Per-class recall ≥ 0.50 for all three labels** (no collapsed class).
- **Fine-tuned macro-F1 ≥ baseline macro-F1 − 0.05** (a 67M-param model lands within 5 points of,
  or beats, a 70B zero-shot model — matching it is already a win given the 1000× size gap).

**Tier 2 — "genuinely useful / deployable" (good-enough-for-a-real-tool):**
- All of Tier 1, **plus `analysis` precision ≥ 0.75**, **plus overall accuracy ≥ 0.70**
  (approaching the human ceiling).
- `analysis` precision is the **hard gate**: the intended product is an *assistive highlighter*
  that surfaces high-quality takes for humans, and in that setting falsely elevating a
  `hot_take`/`reaction` to "analysis" erodes trust faster than missing a good take. So the
  tool ships **human-in-the-loop**, as a soft signal, not an autonomous moderator.

**Failure / not-deployable:** worse than the majority baseline, OR any class recall < 0.40
(collapse), OR `analysis` precision < 0.60 (it can't be trusted to find good takes).

**Self-review — are these criteria objectively checkable?** Yes. Every threshold is a single
number read off the test-set predictions or confusion matrix (accuracy, macro-F1, per-class
recall/precision, and the fine-tuned−baseline delta). At the end I can fill in a table and tick
each box pass/fail with no judgment call — which is the point.

---

## 7. AI Tool Plan

There's no application code to generate in this project, so AI tools help in three specific
places. I've made an explicit decision about each.

### 7.1 Label stress-testing — **DONE (before writing this plan)**
I gave an LLM my label definitions + edge-case description and asked it to generate 10 comments
engineered to straddle the two boundaries, then classified each with R1/R2. Result: **8/10
classified cleanly; 2 exposed gaps**, which I fixed *before* annotating anything:

| # | boundary case | outcome |
|---|---|---|
| 4 | *"Ratings fell every week — 2.1M, 1.8M, 1.5M — clearly the writing turned people off."* | exposed the evidence-plus-leap ambiguity → added **T1 (load-bearing-move)** |
| 6 | *"lmaooo this show is so bad"* | exposed the bare-valence ambiguity → added **T2 (valence-vs-stance)** |

The other 8 (e.g., *"Worst finale ever"* → hot_take, *"This."* → reaction, *"Overrated."* →
hot_take) confirmed the existing rules. Tiebreakers **T1** and **T2** are now in §3. This is the
highest-value AI use in the project: it sharpened the definitions while it was still cheap to
change them.

### 7.2 Annotation assistance — **YES, with guardrails**
- **Decision:** I'll **pre-label** the pool with an LLM applying the §2–3 rubric, then review
  every example, because hand-labeling 240 comments from scratch is the bottleneck.
- **Which tool:** pre-label with **Claude** (this agent), deliberately **not** the Groq
  `llama-3.3-70b` baseline. Using the baseline model to also create the labels would make the
  baseline evaluation circular (it'd be partly graded against its own output). Different model
  families keep the baseline honest.
- **Tracking / disclosure:** the dataset CSV will carry `pre_label`, `final_label`,
  `pre_labeled` (bool), and `changed` (bool). The README's AI-usage section will report how many
  examples were pre-labeled and the pre-label→final agreement rate.
- **Hard guardrail on ground truth:** the **test set** is adjudicated by the human (you)
  independently of any model output, so the numbers in §5–6 are scored against human-authored
  labels — not "what an LLM thinks." I'll also flag the honest methodological caveat that
  AI-assisted labeling means the fine-tuned model is partly distilling the labeler's judgment;
  the human-adjudicated test set is what keeps the evaluation meaningful.

### 7.3 Failure analysis — **YES (planned for M5)**
- **Decision:** after evaluation, I'll hand the full list of misclassified test comments (with
  true vs predicted label and the text) to an LLM and ask it to propose *systematic* error
  patterns — e.g., "confuses `hot_take`/`analysis` when the comment contains numbers but no
  reasoning," "misreads sarcasm as `analysis`," "collapses short comments to `reaction`."
- **What I'll look for:** patterns tied to concrete features — comment length, presence of
  digits/stats, sarcasm/irony, specific shows/topics, and the valence-vs-stance line from T2.
- **How I'll verify (not just trust the AI):** for each proposed pattern I'll pull *every* test
  error matching it and compute its error rate against the base rate for non-matching comments;
  a pattern only goes in the report if it's quantitatively systematic and consistent with the
  confusion matrix. Unverified hunches don't ship.

---

## Appendix — data provenance & reproducibility

- **Source:** pullpush.io comment search, `subreddit=television`. **Unit:** comments.
- **Snapshot:** 595 comments pulled 2026-06-21 (raw pool git-ignored — it contains usernames;
  the committed dataset CSV is the canonical, username-scrubbed artifact).
- **Reproduce:** `python3 data/pull_reddit.py --subreddit television --pages 6 --out data/raw_comments.json`
  (shells out to `curl`, so it works where Python lacks CA certs).

## Roadmap
- **M2** annotate ≥240 (→ ≥200 usable), stratified 70/15/15 split, commit CSV + final counts.
- **M3** fine-tune `distilbert-base-uncased` on Colab T4.
- **M4** zero-shot baseline: Groq `llama-3.3-70b-versatile`, same test set.
- **M5** evaluation report (§5 metrics) + verified failure analysis (§7.3) + learned-vs-intended
  reflection. Stretch candidates: inter-annotator κ, confidence calibration, deployed UI.
