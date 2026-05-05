"""
Production BERT text emotion classifier.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Paths 
_CHECKPOINT_DIR = Path(__file__).parent / "checkpoints" / "bert_mental_health"
_BASE_MODEL_ID  = "j-hartmann/emotion-english-distilroberta-base"

#  Collapse map 
# Handles TWO model variants in one map:


_GOEMOTIONS_COLLAPSE: dict[str, str] = {
    # GoEmotions base model 28 labels 
    "grief":          "hopelessness",
    "remorse":        "hopelessness",
    "disappointment": "hopelessness",
    "nervousness":    "anxiety",
    "fear":           "anxiety",
    "anger":          "anger",
    "annoyance":      "anger",
    "disgust":        "anger",
    "sadness":        "sadness",
    "neutral":        "neutral",
    "realization":    "neutral",
    "confusion":      "neutral",
    "embarrassment":  "neutral",
    "joy":            "positive",
    "love":           "positive",
    "admiration":     "positive",
    "amusement":      "positive",
    "approval":       "positive",
    "caring":         "positive",
    "curiosity":      "positive",
    "desire":         "positive",
    "excitement":     "positive",
    "gratitude":      "positive",
    "optimism":       "positive",
    "pride":          "positive",
    "relief":         "positive",
    "surprise":       "positive",

    # Fine-tuned model 7 labels 

    "normal":               "positive",
    "anxiety":              "anxiety",       
    "depression":           "hopelessness",  
    "suicidal":             "suicidal",      
    "bipolar":              "hopelessness",  
    "personality disorder": "hopelessness",
    "stress":               "anxiety",       
}

# Risk trigger configuration 

CRISIS_LABELS: set[str] = {"suicidal", "hopelessness"}          # → 40 pts
HOPELESSNESS_LABELS: set[str] = {"hopelessness", "suicidal"}    # → 20 pts

_CRISIS_THRESHOLD = 0.40   # suicidal OR hopelessness ≥ this - is_crisis
_HOPELESSNESS_THRESHOLD = 0.35   # suicidal OR hopelessness ≥ this - is_deep_hopelessness

_classifier = None   # singleton loaded at startup


# Output dataclass 
@dataclass
class TextAnalysisResult:
    label:str
    score: float
    all_scores: dict[str, float] = field(default_factory=dict)
    raw_label:str = ""
    is_crisis: bool = False   # 40 risk pts 
    is_deep_hopelessness:bool = False   # 20 risk pts 


#  Loader 
def load_model() -> None:
    """
    Load fine-tuned checkpoint if present, else fall back to HuggingFace base.
    Called once from main.py lifespan on startup.
    """
    global _classifier
    import torch
    from transformers import pipeline

    model_path = str(_CHECKPOINT_DIR) if _CHECKPOINT_DIR.exists() else _BASE_MODEL_ID
    source = "fine-tuned checkpoint" if _CHECKPOINT_DIR.exists() else "HuggingFace base"
    logger.info(f"Loading BERT from {source}: {model_path}")

    device = 0 if torch.cuda.is_available() else -1

    _classifier = pipeline(
        task="text-classification",
        model=model_path,
        tokenizer=model_path,
        top_k=None,       # return ALL label scores for aggregation
        device=device,
        truncation=True,
        max_length=512,
    )
    logger.info(f"BERT ready on {'GPU' if device == 0 else 'CPU'}. Source: {source}")


#  Internal helpers 
def _collapse_label(raw: str) -> str:
    """Map a raw model output label to our clinical taxonomy."""
    return _GOEMOTIONS_COLLAPSE.get(raw.lower(), "neutral")


def _aggregate_scores(raw_results: list[dict]) -> dict[str, float]:
    """
    Collapse raw model labels into clinical categories and sum their scores.
    """
    agg: dict[str, float] = {}
    for item in raw_results:
        key = _collapse_label(item["label"])
        agg[key] = min(1.0, agg.get(key, 0.0) + item["score"])
    return {k: round(v, 4) for k, v in agg.items()}


#  Public interface 
async def classify_text(text: str) -> TextAnalysisResult:
    """
    Classify emotion in text. Runs in a thread pool to avoid blocking the
    FastAPI async event loop (HuggingFace pipelines are synchronous/CPU-bound).
    """
    if _classifier is None:
        raise RuntimeError("BERT not loaded. Call load_model() at startup.")

    loop = asyncio.get_event_loop()
    raw: list[dict] = await loop.run_in_executor(
        None, lambda: _classifier(text[:2048])[0]
    )

    all_scores = _aggregate_scores(raw)
    top_label = max(all_scores, key=lambda k: all_scores[k])
    top_score = all_scores[top_label]
    raw_top = max(raw, key=lambda r: r["score"])

    #  Risk flag evaluation 

    suicidal_score = all_scores.get("suicidal", 0.0)
    hopelessness_score = all_scores.get("hopelessness", 0.0)

    # is_crisis: either suicidal or hopelessness clears the crisis threshold
    is_crisis = (
        suicidal_score >= _CRISIS_THRESHOLD
        or hopelessness_score >= _CRISIS_THRESHOLD
    )

    # is_deep_hopelessness: either bucket clears the (lower) hopelessness threshold
    is_deep_hopelessness = (
        hopelessness_score >= _HOPELESSNESS_THRESHOLD
        or suicidal_score  >= _HOPELESSNESS_THRESHOLD
    )

    result = TextAnalysisResult(
        label=top_label,
        score=top_score,
        all_scores=all_scores,
        raw_label=raw_top["label"],
        is_crisis=is_crisis,
        is_deep_hopelessness=is_deep_hopelessness,
    )

    logger.debug(
        f"BERT | label={top_label} score={top_score:.3f} "
        f"suicidal={suicidal_score:.3f} hopeless={hopelessness_score:.3f} "
        f"is_crisis={is_crisis} is_hopeless={is_deep_hopelessness} "
        f"raw={raw_top['label']}"
    )

    return result