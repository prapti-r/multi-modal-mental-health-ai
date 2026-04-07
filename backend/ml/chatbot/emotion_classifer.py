"""
ml_models/chatbot/emotion_classifier.py
Uses fine-tuned model if available, falls back to base DistilRoBERTa.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("eunoia.emotion")

BASE_MODEL       = "j-hartmann/emotion-english-distilroberta-base"
TRAINED_MODEL    = os.path.join(os.path.dirname(__file__), "trained_model")

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        try:
            from transformers import pipeline
            # Use fine-tuned model if training has been run
            model_path = TRAINED_MODEL if os.path.isdir(TRAINED_MODEL) else BASE_MODEL
            logger.info(f"Loading emotion model from: {model_path}")
            _classifier = pipeline(
                task="text-classification",
                model=model_path,
                top_k=None,
                truncation=True,
                max_length=512,
            )
            logger.info("Emotion model ready.")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            _classifier = None
    return _classifier

EMOTION_MAP = {
    "anger": "angry", "disgust": "disgusted", "fear": "anxious",
    "joy": "happy", "neutral": "neutral", "sadness": "sad", "surprise": "surprised",
    # Mental health dataset labels
    "Anxiety": "anxious", "Depression": "sad", "Suicidal": "distress",
    "Stress": "anxious", "Bipolar": "anxious", "Normal": "neutral",
    "Personality disorder": "anxious",
}

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "can't go on", "no reason to live", "hurt myself", "self harm",
    "self-harm", "cutting myself", "overdose", "not worth living",
]

HIGH_RISK_EMOTIONS = {"sad", "anxious", "angry", "disgusted", "distress"}


def classify_emotion(text: str) -> dict:
    text_lower = text.lower()
    crisis_flag = any(kw in text_lower for kw in CRISIS_KEYWORDS)

    classifier = get_classifier()

    if classifier is None:
        return {
            "dominant_emotion": "distress" if crisis_flag else "neutral",
            "scores": {"neutral": 1.0},
            "crisis_flag": crisis_flag,
            "model": "keyword-fallback",
        }

    try:
        raw = classifier(text[:512])[0]
        scores = {
            EMOTION_MAP.get(r["label"], r["label"].lower()): round(r["score"], 4)
            for r in raw
        }
        dominant = max(scores, key=scores.get)

        if dominant in HIGH_RISK_EMOTIONS and scores[dominant] > 0.6:
            crisis_flag = True

        return {
            "dominant_emotion": dominant,
            "scores": scores,
            "crisis_flag": crisis_flag,
            "model": "DistilRoBERTa-finetuned" if os.path.isdir(TRAINED_MODEL) else "DistilRoBERTa-base",
        }
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return {
            "dominant_emotion": "neutral",
            "scores": {"neutral": 1.0},
            "crisis_flag": crisis_flag,
            "model": "error-fallback",
        }