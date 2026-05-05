"""
CBT-informed response template engine.
"""

import random
from enum import StrEnum


class CbtStrategy(StrEnum):
    REFRAMING             = "reframing"
    VALIDATION            = "validation"
    BEHAVIORAL_ACTIVATION = "behavioral_activation"
    NEUTRAL_CHECKIN       = "neutral_checkin"
    GREETING              = "greeting"
    EMPTY_INPUT           = "empty_input"


_EMOTION_STRATEGY_MAP: dict[str, CbtStrategy] = {
    # Cognitive distortion patterns → Reframing
    "hopelessness":    CbtStrategy.REFRAMING,
    "suicidal":        CbtStrategy.REFRAMING,
    "catastrophizing": CbtStrategy.REFRAMING,
    "self-blame":      CbtStrategy.REFRAMING,
    "worthlessness":   CbtStrategy.REFRAMING,
    "anger":           CbtStrategy.REFRAMING,
    "disgust":         CbtStrategy.REFRAMING,
    "depression":      CbtStrategy.REFRAMING,

    # Raw distress → Validation
    "sadness":   CbtStrategy.VALIDATION,
    "sad":       CbtStrategy.VALIDATION,
    "fear":      CbtStrategy.VALIDATION,
    "anxiety":   CbtStrategy.VALIDATION,
    "stress":    CbtStrategy.VALIDATION,
    "grief":     CbtStrategy.VALIDATION,

    # Neutral states → gentle check-in
    "neutral":   CbtStrategy.NEUTRAL_CHECKIN,
    "normal":    CbtStrategy.NEUTRAL_CHECKIN,

    # Positive or mild states → nudge toward action
    "positive":  CbtStrategy.BEHAVIORAL_ACTIVATION,
    "happy":     CbtStrategy.BEHAVIORAL_ACTIVATION,
    "surprise":  CbtStrategy.BEHAVIORAL_ACTIVATION,
    "calm":      CbtStrategy.BEHAVIORAL_ACTIVATION,
    "joy":       CbtStrategy.BEHAVIORAL_ACTIVATION,
    "normal":    CbtStrategy.BEHAVIORAL_ACTIVATION,

    "bipolar":              CbtStrategy.REFRAMING,
    "personality disorder": CbtStrategy.REFRAMING,
    "stress":               CbtStrategy.VALIDATION,
}

_GREETINGS = {
    "hi", "hello", "hey", "hiya", "howdy", "greetings",
    "good morning", "good afternoon", "good evening", "good night",
    "what's up", "whats up", "sup", "yo",
}

_TEMPLATES: dict[CbtStrategy, list[str]] = {
    CbtStrategy.GREETING: [
        (
            "Hello! I'm really glad you're here. "
            "This is your space to share whatever's on your mind — "
            "whether that's something heavy or just how your day went. "
            "How are you feeling today?"
        ),
        (
            "Hi there! Welcome. I'm here to listen and support you. "
            "There's no right or wrong thing to say — just start wherever feels comfortable. "
            "How has your day been?"
        ),
        (
            "Hey! It's good to see you checking in. "
            "Sometimes just showing up is the hardest part. "
            "What's been on your mind lately?"
        ),
        (
            "Hello! I'm Eunoia, and I'm here with you. "
            "Feel free to share as much or as little as you like. "
            "How are you doing right now?"
        ),
    ],

    CbtStrategy.EMPTY_INPUT: [
        (
            "It looks like you didn't send anything — and that's completely okay. "
            "Sometimes it's hard to find the words. "
            "Whenever you're ready, I'm right here."
        ),
        (
            "No worries if you're not sure what to say. "
            "Take your time. You can start with something small — "
            "even just how you're feeling right now in one word."
        ),
        (
            "It seems like your message was empty. "
            "There's no pressure to say anything specific. "
            "I'm here whenever you're ready to share."
        ),
    ],

    CbtStrategy.NEUTRAL_CHECKIN: [
        (
            "Thanks for checking in! It sounds like things are pretty steady right now. "
            "Is there anything specific on your mind, or anything you'd like to talk through?"
        ),
        (
            "A normal day — that's actually worth acknowledging. "
            "Sometimes the quiet days are the ones that keep us grounded. "
            "Is there anything you'd like to reflect on or explore today?"
        ),
        (
            "Good to hear from you! Even on ordinary days, it's great that you're checking in. "
            "How have you been feeling emotionally over the past few days?"
        ),
        (
            "Sounds like a calm one. "
            "Is there anything you've been thinking about lately — "
            "something you've been meaning to process or talk through?"
        ),
        (
            "A normal day can be a real gift sometimes. "
            "Are there any small things — good or challenging — that stood out for you today?"
        ),
    ],

    CbtStrategy.REFRAMING: [
        (
            "I hear that things feel very heavy right now. "
            "Sometimes our minds present worst-case scenarios as facts. "
            "Let's try to slow that down — what's one thing you know for certain is true right now?"
        ),
        (
            "That sounds really painful. "
            "When we're overwhelmed, it's easy to see everything through a very dark lens. "
            "What would you say to a close friend who was feeling exactly this way?"
        ),
        (
            "I notice you're being quite hard on yourself. "
            "Is there another way to look at this situation — one that's a little more compassionate toward yourself?"
        ),
        (
            "It sounds like your mind is working overtime right now. "
            "Thoughts like these feel very real, but they're not always accurate. "
            "What evidence supports this thought, and what gently pushes back against it?"
        ),
        (
            "When everything feels this dark, it can seem permanent — but feelings do shift. "
            "Can you think of a time, even a small one, when things felt even slightly different?"
        ),
        (
            "It takes courage to sit with feelings this heavy. "
            "You mentioned something really important. "
            "Can we slow down and look at it together? "
            "What's the part that feels most overwhelming right now?"
        ),
    ],

    CbtStrategy.VALIDATION: [
        (
            "Thank you for sharing that with me. "
            "What you're feeling makes complete sense given what you're going through. "
            "You don't have to fix it right now — just letting it out is a brave step."
        ),
        (
            "I'm really glad you felt you could share that. "
            "Those feelings are real and they're valid. "
            "Take your time — I'm here and I'm listening."
        ),
        (
            "That sounds genuinely difficult, and your feelings are completely valid. "
            "Sometimes just naming what we're experiencing helps it feel a little less overwhelming. "
            "Would you like to tell me more?"
        ),
        (
            "I hear you. "
            "Carrying feelings like this is hard, and it makes sense that it weighs on you. "
            "Is there something specific that's been the heaviest part of this?"
        ),
        (
            "What you're going through sounds really tough. "
            "It's okay to feel this way — you don't have to have it all figured out. "
            "I'm here with you."
        ),
        (
            "Thank you for trusting me with this. "
            "Your feelings deserve to be heard. "
            "Can you tell me a little more about what's been going on?"
        ),
    ],

    CbtStrategy.BEHAVIORAL_ACTIVATION: [
        (
            "It's good to hear you're in a better place today! "
            "Small moments of connection or activity can really help sustain that feeling. "
            "Is there one small thing you could do today that usually brings you calm or joy?"
        ),
        (
            "That's a positive sign. "
            "Even tiny steps — a short walk, making tea, reaching out to someone — "
            "can build on good moments. What's one thing you'd like to do for yourself today?"
        ),
        (
            "Great to hear! Let's build on that. "
            "Is there an activity, person, or place that reliably lifts your mood? "
            "Even five minutes of it can make a difference."
        ),
        (
            "I'm glad to hear that. "
            "One thing that helps maintain wellbeing is scheduling small, pleasurable activities. "
            "What's something simple you've been meaning to do but keep putting off?"
        ),
        (
            "That's wonderful. "
            "How do you think you got to this place today? "
            "Understanding what works for us helps us return to it when things get harder."
        ),
    ],
}

_CRISIS_RESPONSE = (
    "I'm really concerned about what you've just shared, and I want you to know "
    "you don't have to face this alone. "
    "Please reach out to a crisis line or one of the professionals in our Therapist Directory — "
    "they are there specifically for moments like this. "
    "Your safety matters more than anything else right now."
)

_MODERATE_RISK_RESPONSE = (
    "It sounds like things are feeling quite overwhelming right now. "
    "I'd encourage you to try a short breathing exercise — "
    "breathe in for 4 counts, hold for 4, and out for 6. "
    "Would you like to talk through what's been building up? "
    "If things continue to feel this intense, speaking with one of the professionals "
    "in our directory could make a real difference."
)


# Greeting detection 

def _is_greeting(text: str) -> bool:
    """Return True if the text is purely a greeting."""
    cleaned = text.strip().lower().rstrip("!?.,")
    return cleaned in _GREETINGS or any(
        cleaned.startswith(g + " ") or cleaned == g for g in _GREETINGS
    )


def _is_empty(text: str) -> bool:
    return not text or not text.strip()


# Public interface 

def get_cbt_response(
    emotion_label: str,
    strategy_hint: CbtStrategy | None = None,
    user_text: str = "",
) -> str:
    """
    Return a CBT-informed response for the detected emotion.
    Checks for greetings and empty input before using emotion label.
    """
    if _is_empty(user_text):
        return random.choice(_TEMPLATES[CbtStrategy.EMPTY_INPUT])

    if _is_greeting(user_text):
        return random.choice(_TEMPLATES[CbtStrategy.GREETING])

    strategy = strategy_hint or _EMOTION_STRATEGY_MAP.get(
        emotion_label.lower(), CbtStrategy.NEUTRAL_CHECKIN
    )
    return random.choice(_TEMPLATES[strategy])


def get_crisis_response() -> str:
    return _CRISIS_RESPONSE


def get_moderate_risk_response() -> str:
    return _MODERATE_RISK_RESPONSE


def get_fallback_response(user_text: str) -> str:
    """
    Fallback Mode — keyword heuristics only, no ML.
    """
    if _is_empty(user_text):
        return random.choice(_TEMPLATES[CbtStrategy.EMPTY_INPUT])

    if _is_greeting(user_text):
        return random.choice(_TEMPLATES[CbtStrategy.GREETING])

    text_lower = user_text.lower()

    crisis_keywords = {
        "suicide", "kill myself", "end it", "don't want to live",
        "self-harm", "hurt myself", "no point", "can't go on",
        "don't want to be here", "not worth living",
    }
    if any(kw in text_lower for kw in crisis_keywords):
        return _CRISIS_RESPONSE

    distress_keywords = {
        "sad", "depressed", "hopeless", "anxious", "scared",
        "alone", "worthless", "empty", "numb", "overwhelmed",
    }
    if any(kw in text_lower for kw in distress_keywords):
        return get_cbt_response("sadness", CbtStrategy.VALIDATION, user_text)

    return get_cbt_response("neutral", CbtStrategy.NEUTRAL_CHECKIN, user_text)