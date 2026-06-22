"""Generate TakeMeter_finetune.ipynb (the Colab notebook) as valid .ipynb JSON.

Building the notebook from Python triple-quoted strings lets json handle all escaping,
so the produced .ipynb is always valid. Run: python3 data/build_notebook.py
"""
import json

cells = []
def md(src):   cells.append(("markdown", src))
def code(src): cells.append(("code", src))

md("""# TakeMeter — Fine-tune DistilBERT + Groq zero-shot baseline

Classifies **r/television** comments by discourse quality: `analysis` / `hot_take` / `reaction`.

**Before running:**
1. `Runtime → Change runtime type → T4 GPU → Save`
2. Add your Groq key in the 🔑 (Secrets) panel as **`GROQ_API_KEY`**, and enable notebook access.
3. `Runtime → Run all`.

The notebook pulls the labeled dataset straight from the public repo, fine-tunes
`distilbert-base-uncased`, runs a zero-shot `llama-3.3-70b-versatile` baseline on the
**same test set**, then writes `evaluation_results.json` and `confusion_matrix.png` and
downloads them (commit those two files to the repo).""")

code("""!pip -q install groq transformers datasets scikit-learn""")

md("""## 1. Config & data
Label ids match the dataset's `label_id` column: analysis=0, hot_take=1, reaction=2.""")

code('''import numpy as np, pandas as pd, json, time, torch

LABELS   = ["analysis", "hot_take", "reaction"]
id2label = {i: l for i, l in enumerate(LABELS)}
label2id = {l: i for i, l in enumerate(LABELS)}

CSV_URL = "https://raw.githubusercontent.com/sindhunaydu/ai201-project3-takemeter/main/data/takemeter_dataset.csv"
df = pd.read_csv(CSV_URL)
df["label_id"] = df["label"].map(label2id)
train_df = df[df.split == "train"].reset_index(drop=True)
val_df   = df[df.split == "val"].reset_index(drop=True)
test_df  = df[df.split == "test"].reset_index(drop=True)
print("device:", "cuda" if torch.cuda.is_available() else "cpu")
print("splits:", len(train_df), len(val_df), len(test_df))
print(df.groupby(["split", "label"]).size().unstack(fill_value=0))''')

md("""## 2. Fine-tune `distilbert-base-uncased`

**Hyperparameter decisions** (small dataset — 150 train examples):
- **Epochs = 6 with `load_best_model_at_end` on validation macro-F1.** With only 150
  examples the model overfits within a few epochs, so instead of trusting a fixed epoch
  count we keep the checkpoint that scores best on the held-out val set. This is the key
  hyperparameter decision.
- **Learning rate = 2e-5** — the standard, stable choice for BERT-family fine-tuning.
- **Batch size = 16**, **max_length = 256** tokens (covers the large majority of comments;
  the longest `analysis` comments truncate — a deliberate speed/coverage tradeoff).""")

code('''from datasets import Dataset
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, DataCollatorWithPadding)
from sklearn.metrics import accuracy_score, f1_score

MODEL, MAX_LEN, SEED = "distilbert-base-uncased", 256, 13
tok = AutoTokenizer.from_pretrained(MODEL)

def to_ds(d):
    ds = Dataset.from_pandas(d[["text", "label_id"]].rename(columns={"label_id": "labels"}),
                             preserve_index=False)
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=MAX_LEN), batched=True)

train_ds, val_ds, test_ds = to_ds(train_df), to_ds(val_df), to_ds(test_df)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL, num_labels=3, id2label=id2label, label2id=label2id)

def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=1)
    return {"accuracy": accuracy_score(p.label_ids, preds),
            "macro_f1": f1_score(p.label_ids, preds, average="macro")}

common = dict(output_dir="out", num_train_epochs=6, learning_rate=2e-5,
              per_device_train_batch_size=16, per_device_eval_batch_size=32,
              load_best_model_at_end=True, metric_for_best_model="macro_f1",
              logging_steps=10, seed=SEED, report_to="none")
try:                       # transformers >= 4.46 renamed the arg
    args = TrainingArguments(eval_strategy="epoch", save_strategy="epoch", **common)
except TypeError:
    args = TrainingArguments(evaluation_strategy="epoch", save_strategy="epoch", **common)

trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds,
                  tokenizer=tok, data_collator=DataCollatorWithPadding(tok),
                  compute_metrics=compute_metrics)
trainer.train()''')

md("""## 3. Evaluate the fine-tuned model on the test set""")

code('''from sklearn.metrics import classification_report, confusion_matrix

pred = trainer.predict(test_ds)
ft_pred = np.argmax(pred.predictions, axis=1)
ft_true = pred.label_ids
print("FINE-TUNED DistilBERT\\n")
print(classification_report(ft_true, ft_pred, target_names=LABELS, digits=3))
ft_report = classification_report(ft_true, ft_pred, target_names=LABELS, output_dict=True)
ft_cm = confusion_matrix(ft_true, ft_pred).tolist()''')

md("""## 4. Zero-shot baseline — Groq `llama-3.3-70b-versatile`

Same test set, no task-specific training. The prompt gives the label definitions and the
R1/R2 decision rule (instructions only — **no labeled examples**, so it stays zero-shot).""")

code('''from groq import Groq
from google.colab import userdata

client = Groq(api_key=userdata.get("GROQ_API_KEY"))

SYSTEM = """You classify comments from the r/television subreddit by DISCOURSE QUALITY into exactly one of three labels.

- analysis: an evaluative or interpretive claim about TV backed by at least one externally checkable specific (a rating, an episode/season count, a date, a named plot event, a production fact, a figure) OR a structured multi-step argument. If you removed the opinion words, a reasoned case would still stand.
- hot_take: a confident, substantive claim about TV (a judgment, ranking, comparison, or factual-sounding assertion) stated WITHOUT checkable support.
- reaction: an expressive, social, or purely informational comment (a joke, exclamation, agreement, question, "name a show" answer, or personal anecdote) that does NOT argue a take about the media.

Decision rule: (1) If there is no substantive standalone claim about a show/episode/performer/industry, answer reaction. (2) Otherwise, if the claim is backed by a checkable specific or a structured argument, answer analysis; if it is asserted without real support, answer hot_take.

Respond with ONLY one word: analysis, hot_take, or reaction."""

def classify(text):
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile", temperature=0, max_tokens=5,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}])
    out = r.choices[0].message.content.strip().lower()
    for l in LABELS:
        if l in out:
            return l, False
    return "reaction", True   # fallback + parse-failure flag

base_pred, parse_fail = [], 0
for t in test_df["text"]:
    lab, failed = classify(t)
    base_pred.append(label2id[lab]); parse_fail += failed
    time.sleep(0.3)          # be gentle with the free tier
base_pred = np.array(base_pred)
print(f"parse failures: {parse_fail}/{len(test_df)}\\n")
print("ZERO-SHOT llama-3.3-70b-versatile\\n")
print(classification_report(ft_true, base_pred, target_names=LABELS, digits=3))
base_report = classification_report(ft_true, base_pred, target_names=LABELS, output_dict=True)
base_cm = confusion_matrix(ft_true, base_pred).tolist()''')

md("""## 5. Confusion matrices → `confusion_matrix.png`""")

code('''import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for ax, cm, title in [(axes[0], ft_cm, "Fine-tuned DistilBERT"),
                      (axes[1], base_cm, "Zero-shot llama-3.3-70b")]:
    ConfusionMatrixDisplay(np.array(cm), display_labels=LABELS).plot(
        ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_title(f"{title}\\nacc={np.trace(cm)/np.sum(cm):.2f}")
    ax.set_xticklabels(LABELS, rotation=30, ha="right")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150, bbox_inches="tight")
plt.show()''')

md("""## 6. Results + success-criteria check → `evaluation_results.json`""")

code('''def acc(rep): return rep["accuracy"]
ft_macro   = ft_report["macro avg"]["f1-score"]
base_macro = base_report["macro avg"]["f1-score"]
ft_recalls = [ft_report[l]["recall"] for l in LABELS]

success = {
    "tier1_macro_f1>=0.60":        ft_macro >= 0.60,
    "tier1_all_class_recall>=0.50": min(ft_recalls) >= 0.50,
    "tier1_within_0.05_of_baseline": ft_macro >= base_macro - 0.05,
    "deploy_analysis_precision>=0.75": ft_report["analysis"]["precision"] >= 0.75,
    "deploy_accuracy>=0.70":        acc(ft_report) >= 0.70,
}

results = {
    "dataset": {"test_size": int(len(test_df)), "labels": LABELS,
                "per_class_support": {l: int(ft_report[l]["support"]) for l in LABELS}},
    "fine_tuned": {"model": "distilbert-base-uncased",
                   "accuracy": acc(ft_report), "macro_f1": ft_macro,
                   "per_class": {l: ft_report[l] for l in LABELS},
                   "confusion_matrix": ft_cm},
    "baseline":   {"model": "llama-3.3-70b-versatile (zero-shot)",
                   "accuracy": acc(base_report), "macro_f1": base_macro,
                   "per_class": {l: base_report[l] for l in LABELS},
                   "confusion_matrix": base_cm, "parse_failures": int(parse_fail)},
    "delta_macro_f1_finetuned_minus_baseline": ft_macro - base_macro,
    "success_criteria": success,
    "hyperparameters": {"base_model": "distilbert-base-uncased", "epochs": 6,
                        "learning_rate": 2e-5, "batch_size": 16, "max_length": 256,
                        "model_selection": "best val macro-F1"},
}
with open("evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps({"fine_tuned_acc": results["fine_tuned"]["accuracy"],
                  "fine_tuned_macro_f1": ft_macro,
                  "baseline_acc": results["baseline"]["accuracy"],
                  "baseline_macro_f1": base_macro,
                  "success": success}, indent=2))''')

md("""## 7. Error analysis — misclassified test comments
Feed this list to an LLM to find *systematic* patterns (then verify each one by counting).""")

code('''print("=== FINE-TUNED errors ===")
for i in np.where(ft_pred != ft_true)[0]:
    print(f"[true={LABELS[ft_true[i]]} | pred={LABELS[ft_pred[i]]}] {test_df.text.iloc[i][:200]}")
print("\\n=== BASELINE errors ===")
for i in np.where(base_pred != ft_true)[0]:
    print(f"[true={LABELS[ft_true[i]]} | pred={LABELS[base_pred[i]]}] {test_df.text.iloc[i][:200]}")''')

md("""## 8. Download the two artifacts (then commit them to the repo)""")

code('''from google.colab import files
files.download("evaluation_results.json")
files.download("confusion_matrix.png")''')

nb = {
    "cells": [
        {"cell_type": t, "metadata": {},
         **({"outputs": [], "execution_count": None} if t == "code" else {}),
         "source": (s if isinstance(s, list) else s.splitlines(keepends=True))}
        for t, s in cells
    ],
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 0,
}
with open("TakeMeter_finetune.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print(f"wrote TakeMeter_finetune.ipynb  ({len(cells)} cells)")
