"""
ml_models/chatbot/cbt_engine.py
─────────────────────────────────
CBT-based response generator.
Selects responses based on intent + emotion + conversation history.

CBT techniques used:
  - Psychoeducation        (explaining what the user is experiencing)
  - Cognitive restructuring (challenging negative thoughts)
  - Behavioural activation  (suggesting small positive actions)
  - Grounding exercises     (5-4-3-2-1, breathing, body scan)
  - Validation + empathy    (always first before advice)
  - Safety planning         (crisis responses)
"""
import random
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE BANKS
# Each entry is a list of variations — randomly picked to avoid repetition
# ─────────────────────────────────────────────────────────────────────────────

RESPONSES = {

    # ── Crisis ────────────────────────────────────────────────────────────────
    "crisis": [
        (
            "I'm really glad you reached out right now — that took courage. "
            "What you're feeling is serious and you deserve immediate support. "
            "Please contact a crisis helpline right away:\n\n"
            "🇳🇵 Nepal: Sathi (1166) | TUTH Psychiatry: 01-4412404\n"
            "🌍 International: befrienders.org | Crisis Text Line: Text HOME to 741741\n\n"
            "You are not alone, and things can get better with the right help. "
            "Are you somewhere safe right now?"
        ),
        (
            "Thank you for trusting me with this. Please know you matter enormously. "
            "Right now, the most important thing is to talk to someone who can really help:\n\n"
            "🇳🇵 Nepal Helpline: 1166 (Sathi)\n"
            "🌍 Befrienders Worldwide: befrienders.org\n\n"
            "Can you tell me — is there someone physically near you right now?"
        ),
    ],

    # ── Greeting ─────────────────────────────────────────────────────────────
    "greeting": [
        "Hello! I'm Eunoia, your mental wellness companion 🌱 I'm here to listen, support, and help you navigate how you're feeling. How are you doing today?",
        "Hi there! I'm so glad you're here. This is a safe space to talk about anything on your mind. How are you feeling right now?",
        "Hey! Welcome. I'm Eunoia — I'm here for you whenever you need to talk. What's on your mind today?",
    ],

    # ── Gratitude ─────────────────────────────────────────────────────────────
    "gratitude": [
        "You're very welcome. Remember, reaching out and talking about your feelings is a real act of self-care. I'm always here when you need me 💙",
        "It means a lot that you shared with me. Take good care of yourself — you deserve it.",
        "Always here for you. Don't hesitate to come back anytime you need to talk 🌿",
    ],

    # ── Goodbye ───────────────────────────────────────────────────────────────
    "goodbye": [
        "Take care of yourself 💙 Remember — every small step towards your wellbeing matters. See you next time.",
        "Goodbye for now. Be kind to yourself today. I'm always here when you want to talk.",
        "See you soon. Keep going — you're doing better than you think 🌱",
    ],

    # ── Venting (sad) ─────────────────────────────────────────────────────────
    "venting_sad": [
        (
            "I hear you, and what you're feeling makes complete sense. "
            "Sadness can feel incredibly heavy, like a weight that's hard to carry alone. "
            "You don't have to carry it alone here.\n\n"
            "Can you tell me a little more about what's been happening for you lately?"
        ),
        (
            "Thank you for sharing that with me — it takes real courage to put those feelings into words. "
            "It sounds like you've been going through a really difficult time.\n\n"
            "I'd like to understand better: has something specific happened, "
            "or has this feeling been building up over time?"
        ),
        (
            "I'm really sorry you're feeling this way. Your feelings are valid and they matter. "
            "Sometimes when we're sad, it can help to gently explore what's underneath that feeling.\n\n"
            "What feels heaviest for you right now?"
        ),
    ],

    # ── Venting (anxious) ─────────────────────────────────────────────────────
    "venting_anxious": [
        (
            "Anxiety can feel overwhelming — like your mind won't stop running even when your body is exhausted. "
            "I want you to know that what you're experiencing is real and valid.\n\n"
            "Let's try something together. Take one slow, deep breath with me. "
            "Breathe in for 4 counts... hold for 4... breathe out for 6. "
            "Did that help even a little?"
        ),
        (
            "It sounds like your anxiety is really high right now. That's really hard to sit with. "
            "One thing that can help is grounding yourself in the present moment.\n\n"
            "Try this: name 5 things you can see around you right now. "
            "Take your time — I'm right here with you."
        ),
        (
            "I hear that you're feeling very anxious. Our nervous system sometimes goes into overdrive, "
            "and it can feel impossible to slow it down.\n\n"
            "Can you tell me what the anxiety feels like in your body? "
            "Where do you feel it most — chest, stomach, head?"
        ),
    ],

    # ── Venting (angry) ───────────────────────────────────────────────────────
    "venting_angry": [
        (
            "It sounds like you're really frustrated and angry right now — and that's okay. "
            "Anger is a valid emotion, and it often tells us something important about what we need.\n\n"
            "What happened that brought up these feelings?"
        ),
        (
            "I can hear how angry you are, and I want you to know that anger is a completely natural response "
            "when we feel wronged, unheard, or overwhelmed.\n\n"
            "Would it help to talk through what's making you feel this way?"
        ),
    ],

    # ── General venting fallback ──────────────────────────────────────────────
    "venting_general": [
        (
            "Thank you for opening up. Whatever you're going through, "
            "you don't have to face it alone.\n\n"
            "I'm here to listen without judgement. Can you tell me more about how you've been feeling?"
        ),
        (
            "It sounds like you're carrying a lot right now. "
            "This is a safe space — take your time and share whatever feels right.\n\n"
            "What's been on your mind most today?"
        ),
    ],

    # ── Help seeking ──────────────────────────────────────────────────────────
    "help_seeking": [
        (
            "I'm here to help. Let's work through this together step by step.\n\n"
            "First — can you describe what's going on in as much detail as feels comfortable? "
            "The more I understand your situation, the better I can support you."
        ),
        (
            "You've taken an important step by asking for help — that shows real self-awareness.\n\n"
            "Tell me what's happening, and we'll think through it together. "
            "There's no rush."
        ),
    ],

    # ── Coping techniques ─────────────────────────────────────────────────────
    "coping_ask": [
        (
            "Here are a few techniques that can help right now:\n\n"
            "**🌬️ Box Breathing (4-4-4-4)**\n"
            "Breathe in for 4 seconds → hold for 4 → breathe out for 4 → hold for 4. Repeat 4 times.\n\n"
            "**🌍 5-4-3-2-1 Grounding**\n"
            "Name: 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.\n\n"
            "**🚶 Behavioural activation**\n"
            "Do one tiny positive thing — make tea, step outside for 2 minutes, text a friend.\n\n"
            "Which of these would you like to try first?"
        ),
        (
            "Absolutely — coping skills are so important. Let's try the **5-4-3-2-1 grounding technique**:\n\n"
            "Look around and tell me:\n"
            "👁️ **5 things you can see**\n"
            "✋ **4 things you can physically feel**\n"
            "👂 **3 things you can hear**\n"
            "👃 **2 things you can smell**\n"
            "👅 **1 thing you can taste**\n\n"
            "Take your time. I'll be right here."
        ),
    ],

    # ── Assessment ask ────────────────────────────────────────────────────────
    "assessment_ask": [
        (
            "Great idea — taking a mental health assessment is a helpful way to understand how you're doing. "
            "I can guide you through the **PHQ-9** (depression screening) or the **GAD-7** (anxiety screening).\n\n"
            "Which would you like to start with, or would you like to do both?"
        ),
        (
            "Mental health assessments are a useful tool — they're not diagnoses, "
            "but they give us a clearer picture of what you might be experiencing.\n\n"
            "Tap the **Assessment** tab to start the PHQ-9 or GAD-7 questionnaire. "
            "I'll be here to talk through the results with you afterwards."
        ),
    ],

    # ── Journal ask ───────────────────────────────────────────────────────────
    "journal_ask": [
        (
            "Journaling is a powerful tool for mental wellness — writing helps process emotions "
            "that are hard to say out loud.\n\n"
            "You can use the **Journal** tab to write freely, or I can give you a prompt to get started. "
            "Would you like a prompt?"
        ),
        (
            "Writing things down is one of the best ways to make sense of what we're feeling. "
            "Head over to the **Journal** tab whenever you're ready.\n\n"
            "Or if you want, just start typing here — I'm listening."
        ),
    ],

    # ── General fallback ──────────────────────────────────────────────────────
    "general": [
        "I'm here and I'm listening. Can you tell me a bit more about what's on your mind?",
        "Thank you for talking to me. I want to make sure I understand you well — can you share more about how you're feeling?",
        "I hear you. This is a safe space. What would be most helpful for you right now — to talk, to vent, or to find some coping strategies?",
    ],

}

# ── Cognitive restructuring prompts (used when venting detected 2+ times) ────
COGNITIVE_RESTRUCTURING = [
    (
        "I want to gently try something with you — it's a technique from CBT called **cognitive restructuring**.\n\n"
        "You mentioned feeling [EMOTION]. When that feeling comes up, what thoughts go through your mind? "
        "For example, does your mind say things like 'I can't do anything right' or 'things will never get better'?"
    ),
    (
        "One thing that can really help is examining the thoughts behind our feelings. "
        "CBT teaches us that our thoughts, feelings, and behaviours are all connected.\n\n"
        "Can you identify one specific thought you've been having that makes you feel worse?"
    ),
]

# ── Follow-up check-ins ────────────────────────────────────────────────────────
FOLLOW_UPS = [
    "How are you feeling now compared to when we started talking?",
    "On a scale of 1–10, how would you rate your mood right now?",
    "Is there anything else you'd like to talk about or get off your chest?",
    "Have you been able to eat and sleep okay recently?",
]


def generate_response(
    intent: str,
    emotion: str,
    turn_count: int = 0,
    previous_intents: Optional[list] = None,
) -> str:
    """
    Main response generator.
    Selects appropriate response bank based on intent + emotion.
    Adds cognitive restructuring after 3+ venting turns.
    """
    previous_intents = previous_intents or []

    # ── Crisis always takes priority ──────────────────────────────────────────
    if intent == "crisis":
        return random.choice(RESPONSES["crisis"])

    # ── Venting — pick emotion-specific bank ──────────────────────────────────
    if intent == "venting":
        if emotion == "sad":
            bank = RESPONSES["venting_sad"]
        elif emotion == "anxious":
            bank = RESPONSES["venting_anxious"]
        elif emotion == "angry":
            bank = RESPONSES["venting_angry"]
        else:
            bank = RESPONSES["venting_general"]

        response = random.choice(bank)

        # After 3+ venting turns, introduce cognitive restructuring
        venting_count = previous_intents.count("venting")
        if venting_count >= 2:
            restructuring = random.choice(COGNITIVE_RESTRUCTURING)
            restructuring = restructuring.replace("[EMOTION]", emotion)
            response = response + "\n\n---\n\n" + restructuring

        return response

    # ── Other intents ─────────────────────────────────────────────────────────
    bank_key = intent if intent in RESPONSES else "general"
    response = random.choice(RESPONSES[bank_key])

    # Add a follow-up check-in after every 4 turns
    if turn_count > 0 and turn_count % 4 == 0:
        response += "\n\n" + random.choice(FOLLOW_UPS)

    return response