"""
ml/training/train_bert.py
──────────────────────────
Fine-tune j-hartmann/emotion-english-distilroberta-base on mental health
conversation datasets to improve sensitivity to clinical language.

Datasets used (from PRD §4):
  • btwitssayan/sentiment-analysis-for-mental-health   (HuggingFace Hub)
  • suchintikasarkar/sentiment-analysis-for-mental-health (Kaggle → local CSV)
  • nguyenletruongthien/mental-health (Kaggle → local CSV)

Fine-tuning strategy:
  Phase 1 — Freeze base, train head only (2 epochs, fast convergence)
  Phase 2 — Unfreeze top 2 transformer layers (3 epochs, domain adaptation)

Output:
  ml/checkpoints/bert_mental_health/   ← loaded by bert_classifier.py

Usage:
  python -m ml.training.train_bert
  python -m ml.training.train_bert --epochs_phase1 3 --epochs_phase2 5
  python -m ml.training.train_bert --data_dir data/mental_health_csvs/
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset, DatasetDict, concatenate_datasets, load_dataset
from sklearn.metrics import f1_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
_ROOT       = Path(__file__).parent.parent.parent          # project root
_CKPT_OUT   = Path(__file__).parent.parent / "checkpoints" / "bert_mental_health"
_BASE_MODEL = "j-hartmann/emotion-english-distilroberta-base"

# ── Label taxonomy ────────────────────────────────────────────────────────────
# We collapse all source dataset labels into this set.
LABELS = ["normal", "anxiety", "depression", "suicidal", "bipolar", "personality disorder", "stress"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# Labels from the mental health datasets → our taxonomy
_MH_LABEL_MAP: dict[str, str] = {
    "Suicidal":             "suicidal",
    "suicidal":             "suicidal",
    "Depression":           "depression",
    "depression":           "depression",
    "Anxiety":              "anxiety",
    "anxiety":              "anxiety",
    "Bipolar":              "bipolar",
    "bipolar":              "bipolar",
    "Bi-Polar":             "bipolar",
    "Personality disorder": "personality disorder",
    "personality disorder": "personality disorder",
    "Stress":               "stress",
    "stress":               "stress",
    "Normal":               "normal",
    "normal":               "normal",
}


# ── Data loading ──────────────────────────────────────────────────────────────

def _map_label(raw: str) -> str | None:
    """Map a raw dataset label to our taxonomy. Returns None to drop the row."""
    return _MH_LABEL_MAP.get(raw.strip())


def load_huggingface_dataset() -> Dataset:
    """
    Load btwitssayan/sentiment-analysis-for-mental-health from HuggingFace Hub.
    Maps labels to our taxonomy and drops unmapped rows.
    """
    logger.info("Loading btwitssayan/sentiment-analysis-for-mental-health from HF Hub...")
    raw = load_dataset("btwitssayan/sentiment-analysis-for-mental-health", split="train")

    # Convert to pandas to easily rename columns
    df = raw.to_pandas()
    if "statement" in df.columns:
        df = df.rename(columns={"statement": "text"})
    if "status" in df.columns:
        df = df.rename(columns={"status": "label"})

    # Map labels and filter
    df["label"] = df["label"].map(_map_label)
    df = df.dropna(subset=["label", "text"])
    df["label"] = df["label"].map(LABEL2ID)

    logger.info(f"HF dataset: {len(df)} examples loaded.")
    return Dataset.from_pandas(df[["text", "label"]])

    # def process(example):
    #     mapped = _map_label(example.get("label", ""))
    #     return {"text": example["text"], "label": mapped}

    # processed = raw.map(process)
    # # Drop rows where label mapping returned None
    # filtered = processed.filter(lambda x: x["label"] is not None)
    # # Convert string labels to int IDs
    # filtered = filtered.map(lambda x: {"label": LABEL2ID[x["label"]]})
    # logger.info(f"HF dataset: {len(df)} examples after filtering.")
    # return filtered


def load_local_csv_datasets(data_dir: Path) -> Dataset | None:
    """
    Load Kaggle mental health CSVs from data_dir.
    Expected columns: 'text' (or 'statement') and 'status' (or 'label').

    Download from:
      kaggle datasets download -d suchintikasarkar/sentiment-analysis-for-mental-health
      kaggle datasets download -d nguyenletruongthien/mental-health
    """
    import pandas as pd

    dfs = []
    for csv_path in data_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_path)
            # Normalise column names across different datasets
            if "statement" in df.columns:
                df = df.rename(columns={"statement": "text"})
            if "status" in df.columns:
                df = df.rename(columns={"status": "label"})
            if "text" not in df.columns or "label" not in df.columns:
                logger.warning(f"Skipping {csv_path.name}: missing 'text' or 'label' column.")
                continue
            df = df[["text", "label"]].dropna()
            df["label"] = df["label"].map(_map_label)
            df = df.dropna(subset=["label"])
            df["label"] = df["label"].map(LABEL2ID)
            dfs.append(df)
            logger.info(f"Loaded {len(df)} examples from {csv_path.name}.")
        except Exception as e:
            logger.warning(f"Failed to load {csv_path.name}: {e}")

    if not dfs:
        return None

    combined = pd.concat(dfs, ignore_index=True)
    return Dataset.from_pandas(combined[["text", "label"]])


def build_dataset(data_dir: Path | None) -> DatasetDict:
    """
    Combine all available datasets, deduplicate, and split into train/val.
    """
    parts: list[Dataset] = []

    # Always try HuggingFace dataset (no local files needed)
    try:
        parts.append(load_huggingface_dataset())
    except Exception as e:
        logger.warning(f"Could not load HF dataset: {e}")

    # Load local CSVs if data_dir provided
    if data_dir and data_dir.exists():
        local_ds = load_local_csv_datasets(data_dir)
        if local_ds:
            parts.append(local_ds)

    if not parts:
        raise RuntimeError(
            "No training data available. "
            "Either the HF dataset failed to load or no local CSVs were found."
        )

    combined = concatenate_datasets(parts)

    # Shuffle and split: 90% train, 10% validation
    combined = combined.shuffle(seed=42)
    split = combined.train_test_split(test_size=0.1, seed=42)
    logger.info(
        f"Dataset ready: {len(split['train'])} train, {len(split['test'])} val examples."
    )
    return DatasetDict({"train": split["train"], "validation": split["test"]})


# ── Tokenisation ──────────────────────────────────────────────────────────────

def tokenize(batch: dict, tokenizer) -> dict:
    return tokenizer(
        batch["text"],
        truncation=True,
        max_length=512,
        padding=False,   # DataCollatorWithPadding handles dynamic padding per-batch
    )


# ── Class weights (handles imbalance — crisis/hopelessness are rare) ──────────

def get_class_weights(dataset: Dataset) -> torch.Tensor:
    labels = np.array(dataset["label"])
    weights = compute_class_weight("balanced", classes=np.unique(labels), y=labels)
    # Upweight crisis and hopelessness by 3x — PRD requires high sensitivity
    for label_name in ("suicidal", "depression"):
        if label_name in LABEL2ID:
            idx = LABEL2ID[label_name]
            weights[idx] *= 3.0
    logger.info(f"Class weights: { {ID2LABEL[i]: round(w, 3) for i, w in enumerate(weights)} }")
    return torch.tensor(weights, dtype=torch.float)


# ── Custom Trainer with class-weighted loss ───────────────────────────────────

class WeightedLossTrainer(Trainer):
    """Overrides compute_loss to apply class weights for imbalanced labels."""

    def __init__(self, *args, class_weights: torch.Tensor, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights.to(self.args.device)

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits  = outputs.logits
        loss_fn = torch.nn.CrossEntropyLoss(weight=self.class_weights)
        loss    = loss_fn(logits, labels)
        return (loss, outputs) if return_outputs else loss


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(eval_pred) -> dict:
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
    crisis_f1 = f1_score(
        labels, preds,
        labels=[LABEL2ID["suicidal"], LABEL2ID["depression"]],
        average="macro",
        zero_division=0,
    )
    logger.info(
        f"\n{classification_report(labels, preds, target_names=LABELS, zero_division=0)}"
    )
    return {
        "macro_f1":             round(macro_f1, 4),
        "crisis_hopeless_f1":   round(crisis_f1, 4),
    }


# ── Phase helpers ─────────────────────────────────────────────────────────────

def _freeze_base(model) -> None:
    """Freeze all layers except the classification head."""
    for name, param in model.named_parameters():
        if "classifier" not in name:
            param.requires_grad = False
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Phase 1: {trainable:,} trainable parameters (head only).")


def _unfreeze_top_layers(model, n_layers: int = 2) -> None:
    """Unfreeze the top N transformer layers for domain adaptation."""
    for name, param in model.named_parameters():
        param.requires_grad = False  # re-freeze everything first

    # DistilRoBERTa has 6 transformer layers (0-5); unfreeze the last N
    for name, param in model.named_parameters():
        if "classifier" in name:
            param.requires_grad = True
        for i in range(6 - n_layers, 6):
            if f"layer.{i}." in name:
                param.requires_grad = True

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Phase 2: {trainable:,} trainable parameters (top {n_layers} layers + head).")


# ── Main training entry point ─────────────────────────────────────────────────

def train(
    epochs_phase1: int = 2,
    epochs_phase2: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    data_dir: Path | None = None,
) -> None:
    """
    Two-phase fine-tuning pipeline.

    Phase 1: Freeze DistilRoBERTa base, train classification head only.
             Fast — domain vocabulary adaptation.
    Phase 2: Unfreeze top 2 transformer layers, continue training.
             Deeper — emotion pattern adaptation.
    """
    logger.info("=== Eunoia BERT Fine-Tuning ===")

    # 1. Load data
    dataset_dict = build_dataset(data_dir)

    # 2. Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(_BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        _BASE_MODEL,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,   # base model has 28 labels; we override with 7
    )

    # 3. Tokenise
    tokenized = dataset_dict.map(
        lambda b: tokenize(b, tokenizer),
        batched=True,
        remove_columns=["text"],
    )
    tokenized.set_format("torch")

    collator      = DataCollatorWithPadding(tokenizer)
    class_weights = get_class_weights(tokenized["train"])

    # ── Phase 1: Head only ────────────────────────────────────────────────
    logger.info(f"\n{'='*50}\nPhase 1 — Head-only training ({epochs_phase1} epochs)\n{'='*50}")
    _freeze_base(model)

    p1_args = TrainingArguments(
        output_dir=str(_CKPT_OUT / "phase1"),
        num_train_epochs=epochs_phase1,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size *2,
        learning_rate=learning_rate,
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="crisis_hopeless_f1",
        greater_is_better=True,
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = WeightedLossTrainer(
        model=model,
        args=p1_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        processing_class=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        class_weights=class_weights,
    )
    trainer.train()

    # ── Phase 2: Top layers + head ────────────────────────────────────────
    logger.info(f"\n{'='*50}\nPhase 2 — Top-layer fine-tuning ({epochs_phase2} epochs)\n{'='*50}")
    _unfreeze_top_layers(model, n_layers=2)

    p2_args = TrainingArguments(
        output_dir=str(_CKPT_OUT / "phase2"),
        num_train_epochs=epochs_phase2,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size *2,
        learning_rate=learning_rate / 5, 
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="crisis_hopeless_f1",
        greater_is_better=True,
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = WeightedLossTrainer(
        model=model,
        args=p2_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        processing_class=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        class_weights=class_weights,
    )
    trainer.train()

    # ── Save final checkpoint ─────────────────────────────────────────────
    _CKPT_OUT.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(_CKPT_OUT))
    tokenizer.save_pretrained(str(_CKPT_OUT))
    logger.info(f"\nFine-tuned model saved to: {_CKPT_OUT}")

    # ── Final evaluation ──────────────────────────────────────────────────
    logger.info("\nFinal evaluation on validation set:")
    metrics = trainer.evaluate()
    logger.info(f"  macro_f1:            {metrics.get('eval_macro_f1', 'N/A')}")
    logger.info(f"  crisis_hopeless_f1:  {metrics.get('eval_crisis_hopeless_f1', 'N/A')}")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune BERT for Eunoia mental health.")
    parser.add_argument("--epochs_phase1", type=int, default=2)
    parser.add_argument("--epochs_phase2", type=int, default=3)
    parser.add_argument("--batch_size",    type=int, default=16)
    parser.add_argument("--lr",            type=float, default=2e-5)
    parser.add_argument(
        "--data_dir",
        type=Path,
        default=None,
        help="Path to directory containing Kaggle mental health CSV files.",
    )
    args = parser.parse_args()

    train(
        epochs_phase1=args.epochs_phase1,
        epochs_phase2=args.epochs_phase2,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        data_dir=args.data_dir,
    )