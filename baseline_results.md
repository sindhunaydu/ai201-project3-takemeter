# Baseline — Zero-shot Groq (Milestone 4)

**Model:** `llama-3.3-70b-versatile` (Groq), zero-shot, temperature 0.
**Test set:** 32 comments — the held-out 15% test split the notebook produced from
[`data/takemeter_dataset.csv`](data/takemeter_dataset.csv) (70/15/15). The *same* split
is reused for the fine-tuned model so the two numbers are directly comparable.
**Parse rate:** 32/32 responses parseable (0% unparseable — the "answer with one word
only" instruction held).

## Results

| class | precision | recall | f1 | support |
|---|---|---|---|---|
| analysis | 0.73 | 0.80 | 0.76 | 10 |
| hot_take | 0.57 | **0.36** | **0.44** | 11 |
| reaction | 0.64 | 0.82 | 0.72 | 11 |
| **accuracy** | | | **0.656** | 32 |
| macro avg | 0.65 | 0.66 | 0.64 | 32 |
| weighted avg | 0.64 | 0.66 | 0.64 | 32 |

**This is the number to beat.** Tier-1 success (planning.md) = fine-tuned macro-F1 ≥
baseline − 0.05 = **≥ 0.59**; the real goal is to beat **0.64** macro-F1 and lift the
`hot_take` recall well above 0.36.

## Inferred prediction structure

The baseline cell didn't print a confusion matrix, but precision/recall/support pin down
the predicted-class counts (TP = recall × support; predicted total = TP / precision):

| true class | caught (TP) | times the model predicted this class |
|---|---|---|
| analysis | 8 / 10 | ~11 |
| hot_take | **4 / 11** | ~7 |
| reaction | 9 / 11 | ~14 |

So the zero-shot model **over-predicts `reaction` (~14 vs 11 true)** and **under-predicts
`hot_take` (~7 vs 11 true)**. Of 11 true hot_takes it caught only 4; the other 7 leaked
out — mostly into `reaction`, some into `analysis`. (Exact matrix will come from the
notebook at M5; paste it and I'll swap these inferred counts for the real ones.)

## Reflection — where the baseline struggled

- **`hot_take` is the failure class (recall 0.36, F1 0.44).** It's defined *negatively* —
  a claim *without* checkable support — so it sits in the middle between "no claim"
  (`reaction`) and "supported claim" (`analysis`). With no calibrated boundary, the
  zero-shot model collapses the middle outward: a bold-but-bare opinion reads either as
  venting (→ `reaction`) or as sounding-reasoned (→ `analysis`).
- **`analysis` and `reaction` are easy** (F1 0.76 and 0.72): structured arguments and
  jokes/agreement are recognizable to a general model with no training.
- **vs my pre-run hypothesis:** I correctly called `analysis`↔`hot_take` the weak boundary
  and `reaction` an easy class. I was **wrong** that the model would over-call `analysis` —
  it actually over-calls **`reaction`**, and hot_takes leak toward reaction more than
  analysis.

## Hypothesis to test after fine-tuning

Fine-tuning should help **most on `hot_take` recall**. Trained on balanced examples, the
model should learn the "claim-present-but-unsupported" middle ground and stop dumping
hot_takes into `reaction`. Concretely I predict: **`hot_take` recall climbs from 0.36
toward ≥ 0.60**, overall **macro-F1 rises above 0.64**, and the `reaction` over-prediction
shrinks. **Falsification:** if `hot_take` stays weak after fine-tuning, that points to the
class being genuinely under-defined / inconsistently labeled — not merely a zero-shot
limitation.

## Prompt used (for reproducibility)

Zero-shot, `{text}` replaced with each test comment, temperature 0:

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
