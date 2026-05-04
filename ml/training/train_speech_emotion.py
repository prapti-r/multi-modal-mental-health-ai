"""
ml/training/train_speech_emotion.py
─────────────────────────────────────
Fine-tune ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition
on RAVDESS + IEMOCAP for improved accuracy on the 8 RAVDESS emotion classes.

Pre-trained model already knows audio features from 53 languages.
Fine-tuning only adapts the classification head + top transformer layers.

Target: ~73% weighted F1 on IEMOCAP 4-class (happy/sad/angry/neutral)
        ~78% weighted F1 on RAVDESS 8-class

Usage:
  python -m ml.training.train_speech_emotion --ravdess_dir data/ravdess/
  python -m ml.training.train_speech_emotion --ravdess_dir data/ravdess/ --iemocap_dir data/iemocap/
"""

import argparse
import logging
import os
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_BASE_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
_CKPT_OUT      = Path(__file__).parent.parent / "checkpoints" / "wav2vec2_speech_emotion"

# RAVDESS emotion codes from filename
_RAVDESS_EMOTION_MAP: dict[int, str] = {
    1: "neutral", 2: "calm", 3: "happy", 4: "sad",
    5: "angry", 6: "fearful", 7: "disgust", 8: "surprised",
}
LABELS   = list(_RAVDESS_EMOTION_MAP.values())
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


# ── Data loading ──────────────────────────────────────────────────────────────

def load_ravdess(ravdess_dir: Path) -> tuple[list[str], list[int]]:
    """Returns (list_of_wav_paths, list_of_label_ids)."""
    paths, labels = [], []
    for wav_path in sorted(ravdess_dir.rglob("*.wav")):
        parts = wav_path.stem.split("-")
        if len(parts) < 3:
            continue
        emotion_code = int(parts[2])
        label_str    = _RAVDESS_EMOTION_MAP.get(emotion_code)
        if label_str:
            paths.append(str(wav_path))
            labels.append(LABEL2ID[label_str])
    logger.info(f"RAVDESS: {len(paths)} samples.")
    return paths, labels


def load_iemocap(iemocap_dir: Path) -> tuple[list[str], list[int]]:
    """Load IEMOCAP — maps 4 emotions to RAVDESS equivalents."""
    _MAP = {"hap": "happy", "sad": "sad", "ang": "angry", "neu": "neutral", "exc": "happy"}
    paths, labels = [], []
    for wav_path in sorted(iemocap_dir.rglob("*.wav")):
        code = wav_path.stem.split("_")[-1].lower()
        if code in _MAP:
            paths.append(str(wav_path))
            labels.append(LABEL2ID[_MAP[code]])
    logger.info(f"IEMOCAP: {len(paths)} samples.")
    return paths, labels


# ── Training ──────────────────────────────────────────────────────────────────

def train(
    ravdess_dir: Path,
    iemocap_dir: Path | None = None,
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 1e-4,
) -> None:
    import torch
    from datasets import Dataset, Audio
    from transformers import (
        AutoFeatureExtractor,
        AutoModelForAudioClassification,
        Trainer,
        TrainingArguments,
        EarlyStoppingCallback,
    )
    from sklearn.utils.class_weight import compute_class_weight

    # 1. Load data
    all_paths, all_labels = load_ravdess(ravdess_dir)
    if iemocap_dir and iemocap_dir.exists():
        ie_paths, ie_labels = load_iemocap(iemocap_dir)
        all_paths += ie_paths
        all_labels += ie_labels

    if not all_paths:
        raise RuntimeError("No audio files found. Check dataset paths.")

    # 2. Split
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        all_paths, all_labels, test_size=0.15, random_state=42, stratify=all_labels
    )

    # 3. HuggingFace Dataset + Audio column (handles resampling to 16kHz automatically)
    train_ds = Dataset.from_dict({"path": train_paths, "label": train_labels})
    val_ds   = Dataset.from_dict({"path": val_paths,   "label": val_labels})

    train_ds = train_ds.cast_column("path", Audio(sampling_rate=16000))
    val_ds   = val_ds.cast_column("path",   Audio(sampling_rate=16000))

    # 4. Feature extractor
    feature_extractor = AutoFeatureExtractor.from_pretrained(_BASE_MODEL_ID)

    def preprocess(batch):
        arrays = [x["array"] for x in batch["path"]]
        inputs = feature_extractor(
            arrays, 
            sampling_rate=16000,
            padding= "max_length", 
            truncation=True, 
            max_length=16000 * 5,  # 5 sec max
            return_tensors="pt",
        )

        if inputs["input_values"].ndim == 3:
            inputs["input_values"] = inputs["input_values"].squeeze(1)

        inputs["labels"] = batch["label"]
        return inputs

    train_ds = train_ds.map(preprocess, batched=True, remove_columns=["path"])
    val_ds   = val_ds.map(preprocess,   batched=True, remove_columns=["path"])
    train_ds.set_format("torch")
    val_ds.set_format("torch")

    # 5. Model — override head for our label count
    model = AutoModelForAudioClassification.from_pretrained(
        _BASE_MODEL_ID,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    # Freeze base feature extractor — only train top transformer layers + head
    model.freeze_feature_encoder()

    # 6. Class weights
    class_weights_arr = compute_class_weight(
        "balanced", classes=np.unique(train_labels), y=train_labels
    )
    class_weights = torch.tensor(class_weights_arr, dtype=torch.float)

    # 7. Weighted trainer
    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels  = inputs.pop("labels")
            outputs = model(**inputs)
            loss    = torch.nn.CrossEntropyLoss(
                weight=class_weights.to(model.device)
            )(outputs.logits, labels)
            return (loss, outputs) if return_outputs else loss

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds    = np.argmax(logits, axis=-1)
        macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
        logger.info(
            "\n" + classification_report(labels, preds, target_names=LABELS, zero_division=0)
        )
        return {"macro_f1": round(macro_f1, 4)}

    # 8. Training args
    args = TrainingArguments(
        output_dir=str(_CKPT_OUT),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=20,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    trainer.train()

    # 9. Save
    _CKPT_OUT.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(_CKPT_OUT))
    feature_extractor.save_pretrained(str(_CKPT_OUT))
    logger.info(f"Fine-tuned Wav2Vec2 saved to: {_CKPT_OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ravdess_dir",  type=Path, required=True)
    parser.add_argument("--iemocap_dir",  type=Path, default=None)
    parser.add_argument("--epochs",       type=int,   default=5)
    parser.add_argument("--batch_size",   type=int,   default=8)
    parser.add_argument("--lr",           type=float, default=1e-4)
    args = parser.parse_args()
    train(args.ravdess_dir, args.iemocap_dir, args.epochs, args.batch_size, args.lr)