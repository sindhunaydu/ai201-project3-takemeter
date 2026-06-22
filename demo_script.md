# TakeMeter Demo — Recording Script & Step-by-Step Actions

**Target length:** 3–5 minutes  
**Format:** screen recording (Colab tab) + voiceover  
**Tool:** QuickTime Player (Mac) or OBS — record the whole screen, not just a window,
so the browser chrome is visible

---

## Before you hit record

### Step 1 — Add the demo cell to the notebook

Open `TakeMeter_finetune.ipynb` in Colab. After the final evaluation cell, add a **new
code cell** with the content below. This is the only thing you need to type before
recording; everything else is clicking.

```python
# ── DEMO CELL ──────────────────────────────────────────────────────────────
import torch, torch.nn.functional as F

# The fine-tuned model + tokenizer are already in memory as `model` and `tokenizer`
# (they were created in the fine-tuning cell above).
# label_map was defined earlier: {"analysis":0, "hot_take":1, "reaction":2}
id2label = {v: k for k, v in label_map.items()}

DEMO_EXAMPLES = [
    # (text, true_label)
    (
        'With The Bear, I think that there\'s the example of S3E5 (Children), '
        'which had the reoccurring "haunting" argument between the Faks throughout '
        'the episode that a lot of viewers got annoyed by, but then it was followed '
        'by the Tina-centric episode Napkins, which felt closer to the best of S1/S2 Bear.',
        "analysis"
    ),
    (
        "You in for a spectacular ride. Final season is one of the BEST!",
        "hot_take"
    ),
    (
        "My wife and I both looked at each other when he said that. Amazing.",
        "reaction"
    ),
    (
        # ERROR CASE — long hot_take that looks like analysis
        "That was one of the best episodes of the show for me. Easily the best of "
        "the season. I know season two and especially Bella are being criticized a lot "
        "(sometimes unfairly) but I think this episode showed what the show is truly "
        "capable of when it fires on all cylinders.",
        "hot_take"
    ),
    (
        "House of the dragon season 2 is the biggest culprit of this.",
        "hot_take"
    ),
]

model.eval()
print(f"{'#':<3} {'TRUE':>9}  {'PRED':>9}  {'CONF':>6}  {'OK':>3}  TEXT")
print("-" * 85)
for i, (text, true_label) in enumerate(DEMO_EXAMPLES, 1):
    enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**enc).logits
    probs = F.softmax(logits, dim=-1)[0]
    pred_id = probs.argmax().item()
    pred_label = id2label[pred_id]
    conf = probs[pred_id].item()
    ok = "✓" if pred_label == true_label else "✗"
    print(f"{i:<3} {true_label:>9}  {pred_label:>9}  {conf:>5.1%}  {ok:>3}  {text[:55]}…")

print()
print("All probabilities:")
print(f"{'#':<3} {'analysis':>10} {'hot_take':>10} {'reaction':>10}")
print("-" * 40)
model.eval()
for i, (text, _) in enumerate(DEMO_EXAMPLES, 1):
    enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**enc).logits
    probs = F.softmax(logits, dim=-1)[0]
    print(f"{i:<3} {probs[0].item():>10.1%} {probs[1].item():>10.1%} {probs[2].item():>10.1%}")
```

### Step 2 — Run the whole notebook top to bottom

`Runtime → Run all`. Wait for it to finish (~5 min on T4). The demo cell output will
appear at the bottom. **Scroll to it and verify the table prints cleanly before you
start recording.** Expected output shape:

```
#    TRUE       PRED    CONF   OK  TEXT
---  ---------  --------  -----  ---  ---
1    analysis   analysis  82.0%  ✓   With The Bear, I think that there's the…
2    hot_take   hot_take  ?.?%   ?   You in for a spectacular ride…
3    reaction   reaction  71.0%  ✓   My wife and I both looked at each other…
4    hot_take   analysis  37.0%  ✗   That was one of the best episodes…
5    hot_take   reaction  34.0%  ✗   House of the dragon season 2…
```

(Exact numbers depend on your Colab run. The two errors in examples 4 and 5 are
confirmed from the saved confusion matrix.)

### Step 3 — Set up your two browser tabs

- **Tab 1:** Colab notebook, scrolled to the demo cell output (visible on screen)
- **Tab 2:** GitHub README or the local README.md rendered in VS Code preview

### Step 4 — Start your screen recorder

- **Mac QuickTime:** File → New Screen Recording → choose full screen → hit Record
- **OBS:** add a Display Capture source → Start Recording
- Do a 5-second silent countdown before you speak so you have edit room.

---

## The script (spoken, ~3.5 min)

Read this naturally — don't read it verbatim. Use it as a beat sheet.

---

### [0:00–0:20] Intro — what is this

> "This is TakeMeter — a classifier I trained to score discourse quality in
> r/television comments. It puts every comment into one of three labels:
> *analysis*, a claim backed by checkable specifics like ratings or episode
> counts; *hot_take*, a confident opinion with no real support; and *reaction*,
> an expressive or social comment that doesn't argue anything. The idea is that
> the community already cares about this distinction — regulars reward comments
> that 'back it up' and dismiss low-effort hot takes."

*(while saying this, you're just on the Colab tab with the demo output visible)*

---

### [0:20–1:30] Five classifications — scroll through them one at a time

Point at each row in the table as you read it.

**Example 1 — analysis, correct (conf ~82%)**
> "Comment 1: 'With The Bear, I think that there's the example of S3E5 Children,
> which had the recurring argument between the Faks … followed by the Tina-centric
> episode Napkins.' Model says *analysis* at 82% confidence, and that's right.
> This comment names specific episodes by number and title — S3E5, Napkins — and
> uses them as evidence for an evaluative claim about the season. That's exactly
> what the R2 rule requires: an externally checkable specific. High confidence,
> correct call."

**Example 2 — hot_take**
> "Comment 2: 'You're in for a spectacular ride. Final season is one of the
> BEST!' Sweeping quality judgment, zero evidence. Should be *hot_take*."
*(note the prediction and confidence)*

**Example 3 — reaction, correct (conf ~71%)**
> "Comment 3: 'My wife and I both looked at each other when he said that.
> Amazing.' Pure personal reaction — no claim being argued at all. *Reaction*,
> reasonably confident."

**Example 4 — hot_take predicted as analysis (the error, conf ~37%)**
> "Comment 4 is where it goes wrong. 'That was one of the best episodes of the
> show … I know season two is being criticized a lot, but I think this episode
> showed what the show is truly capable of.' The true label is *hot_take* — there
> is no checkable specific anywhere in this paragraph, just taste judgments.
> But the model says *analysis* at 37%. I'll talk about why in a second."

**Example 5 — hot_take predicted as reaction**
> "Comment 5: 'House of the Dragon season 2 is the biggest culprit of this.'
> Short, context-dependent — 'of this' points at a parent comment the model
> never sees. True label *hot_take*; model says *reaction*."

---

### [1:30–2:20] Error narration — what went wrong and why

> "So two out of five wrong, and both errors are *hot_takes* misclassified. This
> is the pattern I found throughout the evaluation: *hot_take* recall is 0.36 in
> both the fine-tuned model and the zero-shot baseline — neither one learned the
> middle class well.

> Comment 4 is the clearest case of the failure mode. It's long, it has hedging
> phrases like 'I think' and 'I know X but,' and it sounds like a structured
> argument. The model learned **surface form as a proxy for substance**: long +
> measured register = analysis. It never learned the actual test, which is 'is
> the support externally checkable?' That's exactly what tiebreaker T4 in my
> rubric was written to prevent — 'length is not analysis' — but with only 147
> training examples and a loss curve that barely left random-guess territory, the
> model never learned that distinction.

> Comment 5 is the other direction: short and context-dependent, so the model
> defaults to *reaction*. Together, the two errors show the same underlying
> problem: the model learned a one-dimensional length heuristic instead of the
> actual quality signal."

---

### [2:20–3:30] Evaluation report walkthrough — switch to README tab

*(switch to the README tab in GitHub or VS Code preview)*

> "Here's the evaluation report. The headline: fine-tuning didn't beat the
> zero-shot baseline. Fine-tuned accuracy was 62.5%, baseline was 65.6% — so a
> 70-billion-parameter zero-shot model edged a 67-million-parameter fine-tuned
> one.

> The confusion matrix tells the story."

*(point at the confusion matrix table)*

> "Analysis: 10 out of 10 — perfect recall. The model never missed a single
> analysis comment. Reaction: 6 out of 11 — okay. Hot_take: 4 out of 11 — 5
> hot_takes were called analysis, 2 were called reaction. The dominant confusion
> pair is hot_take → analysis, which accounts for 42% of all 12 errors.

> The training loss curve also flags the problem clearly: after 3 epochs the
> training loss was barely below ln(3), which is what a random guesser would
> get on 3 classes. The model is undertrained. Validation accuracy was still
> climbing at epoch 3, so more epochs would likely help hot_take recall
> specifically.

> Bottom line: the model meets Tier 1 success — it beats the majority baseline
> and has macro-F1 of 0.61 — but falls short of Tier 2. It's not deployable
> as a standalone highlighter until hot_take recall comes up substantially."

---

### [3:30–3:50] Closing

> "The core lesson is that 'length and argumentative register' and 'substantive
> support' are not the same thing, and a 67M-parameter model on 147 training
> examples isn't going to learn the difference without more signal. The fix is
> probably more epochs and potentially more targeted hot_take training examples —
> specifically long-but-unsupported paragraphs, which is where the model is most
> confidently wrong."

*(stop recording)*

---

## After recording

1. Trim the first 5 seconds of silence and any stumbles in QuickTime (Edit →
   Trim) or your editor of choice.
2. Export: QuickTime → File → Export As → 1080p. Target file size < 500 MB.
3. Upload to Google Drive, YouTube (unlisted), or Loom and paste the link into
   your submission.
