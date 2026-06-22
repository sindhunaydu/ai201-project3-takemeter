# TakeMeter — Planning

A fine-tuned classifier that scores **discourse quality** in **r/television** by
sorting comments along a "how much does this comment actually argue its take?"
spine: `analysis` → `hot_take` → `reaction`.

---

## Milestone 1 — Community & Label Taxonomy

### The community: r/television

r/television (~19M members) is a general TV-discussion subreddit. Submissions are
mostly **news headlines and links** (renewals, casting, trailers, ratings), so the
actual opinions — the *takes* — live in the **comments**. That is why our unit of
classification is the **comment**, not the submission.

The community has a strong, self-aware norm about take quality: regulars routinely
praise comments that "actually back it up" and dismiss "low-effort hot takes" and
pure "circle-jerk" reaction posts. So a quality taxonomy isn't something we're
imposing from outside — it mirrors a distinction the community already polices.

### How I read the community first (no labels from memory)

I pulled **595 real r/television comments** from the
[pullpush.io](https://pullpush.io) research archive (free, no-auth Pushshift
successor) via [`data/pull_reddit.py`](data/pull_reddit.py) on 2026-06-21, then
read a varied sample of **42 comments** spread across length buckets
(short `<70` chars, medium `70–320`, long `≥320`) and across the score range
(from −37 to +46). Reading the actual text — not my assumptions — is what produced
the patterns below. Three kinds of comment kept recurring:

1. Comments that **argue** a point with checkable specifics (episode ratings,
   season/episode counts, production history, plot events, box-office numbers).
2. Comments that **assert a judgment** confidently but with no real support.
3. Comments that are **expressive or social** — jokes, one-word answers,
   agreement, questions — and aren't really arguing anything.

That maps onto a quality gradient, which is exactly what "discourse quality" means
here.

### The labels (3, mutually exclusive, exhaustive)

The spine is a single question: **how much does the comment do to support a take
about TV?** More support → `analysis`; a bare take → `hot_take`; no take at all →
`reaction`.

---

#### `analysis` — an evaluative/interpretive claim about TV **backed by at least one externally checkable specific or a structured multi-step argument.**

If you stripped the opinion words out, a reasoned case would still be standing.
Checkable specifics = ratings, episode/season counts, dates, named plot events,
production facts, box-office figures, cross-show comparisons used *as evidence*.

**Clear example 1** (score 3):
> "HBO needed 7 seasons. GRRM said it could go to like 14. HBO thought 10. They
> gave 8 … S8 is only 6 episodes. You could take 3 of those episodes and put them
> in S7 and you'd have one NORMAL season length."
*(specific episode/season counts marshalled into an argument)*

**Clear example 2** (score 6):
> "They top this in S10, there's a terrible Carol & Daryl filler episode with a
> deserved 4.1 rating which is immediately followed by Negan's backstory with a 9.2
> rating …"
*(cites specific episode ratings as evidence)*

**Uncertain case** (score 15):
> "There was such a massive jump in overall filmmaking quality for this episode …
> It's so obvious that Neil Druckman directed and wrote this episode. His ability
> to craft scenes is night and day compared to the others."
Could be `hot_take` — "massive jump" / "night and day" are subjective. But it rests
on a **verifiable production fact** (Druckman wrote/directed it) and reasons *from*
that fact about craft. → **analysis** (see decision rule R2).

---

#### `hot_take` — a confident, substantive claim about TV (a judgment, ranking, or factual-sounding assertion) **stated without checkable support.**

The comment tells you *what* the author thinks, not a developed, verifiable *why*.
The claim may well be true — it's the lack of support that defines the label, not
correctness.

**Clear example 1** (score −2):
> "So you are saying it is a standard Tom Hardy Project. It is wild how much love he
> gets when pretty much everything he does is trash."
*(sweeping evaluative claim, zero evidence)*

**Clear example 2** (score 8):
> "Way too far down. It's easily my favourite terrible person show."
*(a ranking judgment asserted flatly)*

**Uncertain case** (score 6):
> "The episodes without him have been mediocre at best, there aren't any strong
> actor to compensate his loss."
It offers a *reason* ("no strong actor to compensate"), which flirts with
`analysis`. But the reason is itself an unsupported assertion — no episode, metric,
or specific named. → **hot_take** (fails R2: no externally checkable specific).

---

#### `reaction` — an expressive, social, or purely informational comment that **does not advance an evaluative argument about the media.**

Emotion, jokes, one-liners, agreement/disagreement, "name a show" answers,
plot questions, simple factual statements/corrections, and personal anecdotes all
live here. The unifying property: **no take being argued.** This is the largest
natural bucket, but it is defined positively (expressive/social/informational), not
as a catch-all "other."

**Clear example 1** (score 11):
> "BEES?!"
*(pure exclamation / reference, no claim)*

**Clear example 2** (score 0):
> "i agree completely with everything you said"
*(social agreement, contributes no independent take)*

**Uncertain case** (score 2):
> "Nailed it. One of the few perfect TV finales."
"Nailed it" reads as reaction/agreement, but "one of the few perfect TV finales"
is a standalone evaluative claim. → **hot_take**, not reaction (see decision rule
R1): any standalone judgment about the media pulls a comment up out of `reaction`.

---

### Decision procedure (makes the labels mutually exclusive)

Apply in order; the first matching rule wins. This is what I'll hand to any
second annotator.

- **R1 — Is there a take?** Does the comment make a substantive standalone claim
  about a show/episode/performer/industry (judgment, ranking, or factual-sounding
  assertion)?
  - **No** → `reaction`. *(emotion, jokes, agreement, questions, "name a show"
    answers, simple facts/corrections, personal stories)*
  - **Yes** → go to R2.
- **R2 — Is the take supported?** Is it backed by ≥1 externally checkable specific
  (rating, count, date, named plot event, production fact, figure) **or** a
  structured multi-step argument that would stand with the opinion words removed?
  - **Yes** → `analysis`.
  - **No** (asserted, vague, or decorative support) → `hot_take`.

**Tiebreakers** (from real borderline cases I hit while validating):

- **Incidental-judgment rule:** if an evaluative aside sits inside an otherwise
  expressive/personal/social comment, label by the comment's *primary function*.
  The judgment must be the point to count as `hot_take`.
  (e.g. *"funny how the TV show made me appreciate the awful part 2 a bit more"* →
  `reaction`: the point is a personal experience, "awful" is an aside.)
- **Length ≠ analysis:** a long comment whose load-bearing claims are *all*
  unsupported taste judgments is an elaborated opinion, not analysis. Analysis
  needs at least one externally checkable fact. (Resolves the BBT case below.)
- **Implicit/rhetorical claims count** as takes under R1 (e.g. *"Name a single
  instance where game Ellie was likable"* asserts "Ellie is unlikable" → R2 →
  `hot_take`).

### Three genuinely difficult cases (and what I decided)

1. **The Big Bang Theory laugh-track essay** (long, score 0): *"…BBT is just, not in
   my opinion, a funny show … Mash, Cheers, Seinfeld, Frasier … are all great shows
   and the laugh track adds something … Shifting Gears is not funny and the laugh
   track feels inauthentic."* — It's long and lists many shows, which *looks* like
   analysis, and it even has a thesis (laugh-track quality tracks writing quality).
   But every load-bearing premise ("X is funny, Y isn't") is itself a taste
   judgment — there's no externally checkable fact. **Decided `hot_take`** via the
   "length ≠ analysis" tiebreaker. This is the single most important boundary in the
   project: it stops the model from learning "long = analysis."

2. **"Nailed it. One of the few perfect TV finales."** (score 2) — `reaction` vs
   `hot_take`. The opener is pure agreement; the second clause is a quality verdict.
   **Decided `hot_take`** (R1: a standalone evaluative claim outranks the reaction
   framing).

3. **"The episodes without him have been mediocre at best, there aren't any strong
   actor to compensate."** (score 6) — `analysis` vs `hot_take`. It *has* a reason,
   which is more than a bare opinion. But the reason is unverifiable assertion.
   **Decided `hot_take`** (R2: a reason that is itself unsupported opinion is not
   evidence).

### Mutual-exclusivity & distribution check

I labeled a **fresh** random sample of 20 comments (different RNG seed from the
reading sample) using the procedure above:

| label | count | share |
|---|---|---|
| reaction | 9 | 45% |
| analysis | 6 | 30% |
| hot_take | 5 | 25% |

- **Exhaustive:** 20/20 received a real label — no "other" needed (>90% target met).
- **Mutually exclusive:** ~13/20 were unambiguous on first read; the ~7 borderline
  cases each resolved to exactly one label via R1/R2 + tiebreakers. The rules, not
  gut feel, do the assigning.
- **Distribution:** all three labels clear the 20% floor and none approaches the
  80% danger zone. `reaction` is the natural majority. **Action for Milestone 2:**
  oversample medium/long comments so the 200-example set lands closer to balanced
  (target ≥30% each); document this sampling bias honestly in the README.

### Two–three sentence summary (for the README)

> TakeMeter classifies comments in **r/television** by discourse quality along a
> single spine — how much a comment actually argues its take: **`analysis`**
> (a TV claim backed by checkable specifics like ratings, episode counts, or plot
> events), **`hot_take`** (a confident judgment asserted with no real support), and
> **`reaction`** (expressive or social comments — jokes, agreement, one-liners —
> that argue nothing). The distinction matters because the community itself polices
> it: regulars reward takes that are "backed up" and dismiss low-effort hot takes
> and circle-jerk reactions, so the labels track a quality line people there
> already care about.

---

## Data provenance

- **Source:** pullpush.io comment search for `subreddit=television` (free research
  archive; no Reddit auth — Reddit's own API/site is bot-walled from this
  environment).
- **Unit:** comments (takes live in comments; submissions are mostly headlines).
- **Pulled:** 2026-06-21, 595 comments over 6 paginated pages →
  [`data/raw_comments.json`](data/raw_comments.json).
- **Filtering for reading:** dropped `[deleted]`/`[removed]`/empty/link-only
  (587 usable of 595).
- **Reproduce:** `python3 data/pull_reddit.py --pages 6 --out raw_comments.json`

## Roadmap (next milestones)

- **M2 — Dataset:** annotate ≥200 comments (train/val/test split), balanced toward
  ≥30% per label; document labeling process, distribution, and ≥3 hard cases.
- **M3 — Fine-tune** `distilbert-base-uncased` on the labeled set (Colab T4).
- **M4 — Baseline:** zero-shot `llama-3.3-70b-versatile` (Groq) on the same test set.
- **M5 — Evaluation:** accuracy + per-class F1, confusion matrix, ≥3 error analyses,
  and a reflection on learned-vs-intended.
- **Stretch (candidates):** inter-annotator kappa, confidence calibration,
  systematic error-pattern analysis, deployed inference UI.
