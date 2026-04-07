"""
ml_models/chatbot/intent_classifier.py
────────────────────────────────────────
Classifies user message intent using pattern matching + emotion signals.
No extra model needed — runs on CPU instantly.

Intents:
  crisis          → immediate danger / self-harm
  greeting        → hello, hi, how are you
  venting         → expressing feelings, no specific ask
  help_seeking    → asking for advice / what to do
  assessment_ask  → asking about PHQ-9, GAD-7, quiz
  gratitude       → thank you, thanks
  goodbye         → bye, see you
  journal_ask     → wants to write / reflect
  coping_ask      → breathing, relaxation, grounding
  general         → fallback
"""
import re
from typing import Tuple

INTENT_PATTERNS = [
    ("crisis", [
        r"suicid", r"kill\s*my\s*self", r"end\s*my\s*life", r"want\s*to\s*die",
        r"hurt\s*my\s*self", r"self[\s\-]?harm", r"no\s*reason\s*to\s*live",
        r"can'?t\s*go\s*on", r"not\s*worth\s*(living|it)", r"cutting\s*my\s*self",
    ]),
    ("greeting", [
        r"\bhello\b", r"\bhi\b", r"\bhey\b", r"good\s*(morning|afternoon|evening|night)",
        r"how\s*are\s*you", r"how\s*r\s*u",
    ]),
    ("gratitude", [
        r"\bthank(s| you)\b", r"\bthx\b", r"\bty\b", r"appreciate",
    ]),
    ("goodbye", [
        r"\bbye\b", r"\bgoodbye\b", r"see\s*you", r"talk\s*later", r"gotta\s*go",
    ]),
    ("assessment_ask", [
        r"phq[\s\-]?9", r"gad[\s\-]?7", r"quiz", r"questionnaire", r"test\s*my",
        r"assess", r"score", r"how\s*depressed", r"am\s*i\s*(depressed|anxious)",
    ]),
    ("coping_ask", [
        r"breathing", r"relax", r"calm\s*down", r"grounding", r"meditat",
        r"what\s*can\s*i\s*do", r"how\s*do\s*i\s*(cope|deal|handle|manage)",
        r"help\s*me\s*(calm|relax|feel better)",
    ]),
    ("journal_ask", [
        r"write", r"journal", r"diary", r"reflect", r"record\s*my",
        r"want\s*to\s*express", r"put\s*(it|this)\s*into\s*words",
    ]),
    ("help_seeking", [
        r"what\s*should\s*i", r"what\s*do\s*i\s*do", r"advice",
        r"help\s*me", r"i\s*need\s*help", r"guide\s*me", r"suggest",
    ]),
    ("venting", [
        r"i\s*(feel|felt|am|was|have been)\s*(so|very|really)?\s*(sad|depressed|anxious|stressed|overwhelmed|lonely|tired|hopeless|worthless|empty)",
        r"i\s*can'?t\s*(sleep|eat|focus|stop\s*crying)",
        r"everything\s*(is|feels)\s*(wrong|terrible|awful|hard)",
        r"nobody\s*(understands?|cares?|listens?)",
        r"i\s*(hate|don'?t\s*like)\s*(my\s*life|myself|everything)",
    ]),
]


def classify_intent(text: str, dominant_emotion: str = "neutral") -> Tuple[str, float]:
    """
    Returns (intent_label, confidence_score).
    Tries pattern matching first, falls back to emotion-based inference.
    """
    text_lower = text.lower().strip()

    for intent, patterns in INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text_lower):
                # Crisis always gets max confidence
                confidence = 0.99 if intent == "crisis" else 0.85
                return intent, confidence

    # Emotion-based fallback inference
    emotion_intent_map = {
        "sad":        ("venting", 0.65),
        "anxious":    ("venting", 0.65),
        "angry":      ("venting", 0.60),
        "disgusted":  ("venting", 0.60),
        "happy":      ("greeting", 0.50),
        "surprised":  ("general", 0.45),
        "neutral":    ("general", 0.40),
    }

    return emotion_intent_map.get(dominant_emotion, ("general", 0.40))