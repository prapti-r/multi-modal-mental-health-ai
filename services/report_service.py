"""
services/report_service.py
───────────────────────────
Late Fusion weekly report generation and therapist directory.

Implements PRD §7.2 (MHI formula) and §7.3 (weighted late fusion + fallback).

── MHI Formula (PRD §7.2) ───────────────────────────────────────────────────
  MHI = 1.0 − clamp( μ(RP_daily) / 100, 0, 1 )

  Where μ(RP_daily) = average daily risk points over the 7-day window.
  MHI = 1.0 → perfectly stable.   MHI = 0.0 → crisis level.

── Standard Channel Weights (PRD §7.3) ──────────────────────────────────────
  Subjective  (mood logs + journal sentiment)     → 40%
  Cognitive   (chat BERT analysis)                → 35%
  Physiological (voice + facial features)         → 25%

── Dynamic Fallback Redistribution (PRD §7.3) ───────────────────────────────
  If physiological data is absent for the week:
    w'_channel = w_original + (w_p × w_original / (w_s + w_c))
  Results in: Subjective → 53.3%,  Cognitive → 46.7%

── Report Caching Policy ─────────────────────────────────────────────────────
  Completed weeks (today > Sunday of that week): report is cached permanently.
  In-progress weeks: report is ALWAYS regenerated on each request so that
  newly logged mood, journal, and chat data is immediately reflected.
  The stale in-progress report is deleted before regeneration.

── Qualitative Narrative ─────────────────────────────────────────────────────
  Generated from the MHI value and dominant risk sources —
  no external LLM dependency, deterministic and fast.

Public interface:
  get_or_generate_weekly_report(db, user_id)   → LateFusionReport
  get_therapists(db)                           → list[Therapist]
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.ai_analysis_result import AiAnalysisResult
from models.chat_message import ChatMessage
from models.chat_session import ChatSession
from models.journal import Journal
from models.late_fusion_report import LateFusionReport
from models.mood_log import MoodLog
from models.risk_log import RiskLog, RiskLevel
from models.therapist import Therapist


# ── Weight constants (PRD §7.3) ────────────────────────────────────────────────
_W_SUBJECTIVE    = 0.40
_W_COGNITIVE     = 0.35
_W_PHYSIOLOGICAL = 0.25

# Fallback weights when physiological channel is missing
_W_SUBJ_FALLBACK = round(_W_SUBJECTIVE  + (_W_PHYSIOLOGICAL * _W_SUBJECTIVE  / (_W_SUBJECTIVE + _W_COGNITIVE)), 4)  # 53.3%
_W_COGN_FALLBACK = round(_W_COGNITIVE   + (_W_PHYSIOLOGICAL * _W_COGNITIVE   / (_W_SUBJECTIVE + _W_COGNITIVE)), 4)  # 46.7%

# MHI thresholds → prediction labels
_MHI_LABELS: list[tuple[float, str]] = [
    (0.25, "Crisis"),
    (0.45, "Declining"),
    (0.65, "At Risk"),
    (0.85, "Cautious"),
    (1.01, "Stable"),
]


# ── Internal data collectors ───────────────────────────────────────────────────

async def _collect_mood_scores(
    db: AsyncSession, user_id: UUID, start: date, end: date
) -> list[int]:
    """Return all mood_score values logged in the window."""
    result = await db.execute(
        select(MoodLog.mood_score).where(
            MoodLog.user_id == user_id,
            func.date(MoodLog.logged_at) >= start,
            func.date(MoodLog.logged_at) <= end,
        )
    )
    return list(result.scalars().all())


async def _collect_journal_sentiments(
    db: AsyncSession, user_id: UUID, start: date, end: date
) -> list[float]:
    """Return all non-null sentiment_score values from journals in the window."""
    result = await db.execute(
        select(Journal.sentiment_score).where(
            Journal.user_id == user_id,
            Journal.sentiment_score.isnot(None),
            func.date(Journal.created_at) >= start,
            func.date(Journal.created_at) <= end,
        )
    )
    return [float(s) for s in result.scalars().all()]


async def _collect_risk_points(
    db: AsyncSession, user_id: UUID, start: date, end: date
) -> list[int]:
    """Return all total_points from risk_logs in the window."""
    result = await db.execute(
        select(RiskLog.total_points).where(
            RiskLog.user_id == user_id,
            func.date(RiskLog.created_at) >= start,
            func.date(RiskLog.created_at) <= end,
        )
    )
    return list(result.scalars().all())


async def _collect_ai_analyses(
    db: AsyncSession, user_id: UUID, start: date, end: date
) -> list[AiAnalysisResult]:
    """Return all AiAnalysisResult rows from the user's chat messages in the window."""
    result = await db.execute(
        select(AiAnalysisResult)
        .join(ChatMessage, AiAnalysisResult.message_id == ChatMessage.id)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(
            ChatSession.user_id == user_id,
            func.date(ChatMessage.created_at) >= start,
            func.date(ChatMessage.created_at) <= end,
        )
    )
    return list(result.scalars().all())


async def _get_existing_report(
    db: AsyncSession, user_id: UUID, start: date, end: date
) -> LateFusionReport | None:
    """Return an existing report for the same period if one exists."""
    result = await db.execute(
        select(LateFusionReport).where(
            LateFusionReport.user_id == user_id,
            LateFusionReport.report_period_start == start,
            LateFusionReport.report_period_end == end,
        )
    )
    return result.scalar_one_or_none()


# ── Score normalisation helpers ────────────────────────────────────────────────

def _normalise_mood(scores: list[int]) -> float:
    """
    Convert raw mood scores (1-10) to a 0-1 risk contribution.
    Lower mood → higher risk.  Returns 0.0 if no data.
    """
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    # Invert: score=1 → risk=1.0,  score=10 → risk=0.0
    return round(1.0 - (avg - 1) / 9.0, 4)


def _normalise_sentiment(scores: list[float]) -> float:
    """
    Convert BERT sentiment scores (-1 to 1) to a 0-1 risk contribution.
    Negative sentiment → higher risk.  Returns 0.0 if no data.
    """
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    # sentiment ∈ [-1, 1]; map to risk ∈ [0, 1]
    return round((1.0 - avg) / 2.0, 4)


def _normalise_text_analysis(analyses: list[AiAnalysisResult]) -> float:
    """
    Aggregate BERT text_analysis scores from AI chat analyses.
    Returns average crisis/hopelessness contribution (0-1).
    """
    if not analyses:
        return 0.0
    crisis_labels = {"crisis", "hopelessness", "anxiety"}
    scores: list[float] = []
    for a in analyses:
        if not a.text_analysis:
            continue
        label = a.text_analysis.get("label", "neutral")
        score = float(a.text_analysis.get("score", 0.0))
        if label in crisis_labels:
            scores.append(score)
        else:
            scores.append(0.0)
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def _normalise_physiological(analyses: list[AiAnalysisResult]) -> float | None:
    """
    Aggregate distress signals from facial_emotions and voice_features.
    Returns None if no physiological data is available this week
    (triggers the fallback weight redistribution — PRD §7.3).
    """
    distress_scores: list[float] = []
    distress_emotion_keys = {"anger", "anxiety", "sadness"}

    for a in analyses:
        # Facial
        if a.facial_emotions:
            all_em = a.facial_emotions.get("all_emotions", {})
            d = sum(all_em.get(k, 0.0) for k in distress_emotion_keys)
            distress_scores.append(min(d, 1.0))

        # Voice
        if a.voice_features:
            all_em = a.voice_features.get("all_emotions", {})
            d = sum(all_em.get(k, 0.0) for k in distress_emotion_keys)
            distress_scores.append(min(d, 1.0))

    if not distress_scores:
        return None   # triggers fallback weight redistribution

    return round(sum(distress_scores) / len(distress_scores), 4)


# ── MHI calculation (PRD §7.2) ────────────────────────────────────────────────

def _calculate_mhi(avg_daily_risk_points: float) -> float:
    """
    PRD §7.2:  MHI = 1.0 − clamp( μ(RP_daily) / 100,  0,  1 )
    """
    clamped = max(0.0, min(1.0, avg_daily_risk_points / 100.0))
    return round(1.0 - clamped, 4)


def _get_prediction_label(mhi: float) -> str:
    for threshold, label in _MHI_LABELS:
        if mhi < threshold:
            return label
    return "Stable"


# ── Weighted fusion (PRD §7.3) ────────────────────────────────────────────────

def _fuse_channels(
    subjective_risk: float,
    cognitive_risk: float,
    physiological_risk: float | None,
) -> float:
    """
    Apply weighted late fusion to produce a single composite risk score (0-1).
    Uses fallback weights if physiological channel is missing.

    Returns composite_risk ∈ [0, 1]
    """
    if physiological_risk is not None:
        # Standard weights (PRD §7.3)
        composite = (
            subjective_risk    * _W_SUBJECTIVE +
            cognitive_risk     * _W_COGNITIVE  +
            physiological_risk * _W_PHYSIOLOGICAL
        )
    else:
        # Dynamic redistribution — physiological channel absent (PRD §7.3)
        composite = (
            subjective_risk * _W_SUBJ_FALLBACK +
            cognitive_risk  * _W_COGN_FALLBACK
        )
    return round(min(1.0, max(0.0, composite)), 4)


# ── Qualitative narrative generator ───────────────────────────────────────────

def _build_qualitative_report(
    mhi: float,
    prediction_label: str,
    mood_scores: list[int],
    sentiment_scores: list[float],
    risk_points: list[int],
    has_physiological: bool,
    is_crisis: bool,
) -> str:
    """
    Build a deterministic, personalised weekly narrative from aggregated data.
    No external LLM — fast, auditable, and always available.
    """
    lines: list[str] = []

    # ── Opening statement ─────────────────────────────────────────────────
    opening_map = {
        "Stable":   "Your wellbeing this week has been in a good place overall.",
        "Cautious": "This week shows some signs worth paying attention to.",
        "At Risk":  "This week's patterns suggest you've been carrying some emotional weight.",
        "Declining":"Several indicators this week point to increased distress.",
        "Crisis":   "This week's data shows significant distress signals that concern us.",
    }
    lines.append(opening_map.get(prediction_label, "Here is your weekly wellbeing summary."))

    # ── Mood commentary ───────────────────────────────────────────────────
    if mood_scores:
        avg_mood = sum(mood_scores) / len(mood_scores)
        if avg_mood >= 7.0:
            lines.append(
                f"Your average mood score of {avg_mood:.1f}/10 reflects a positive week."
            )
        elif avg_mood >= 5.0:
            lines.append(
                f"Your average mood score of {avg_mood:.1f}/10 suggests moderate stability."
            )
        else:
            lines.append(
                f"Your average mood score of {avg_mood:.1f}/10 indicates this has been a difficult week."
            )
    else:
        lines.append("No mood logs were recorded this week — try to check in daily.")

    # ── Journal sentiment commentary ──────────────────────────────────────
    if sentiment_scores:
        avg_sent = sum(sentiment_scores) / len(sentiment_scores)
        if avg_sent >= 0.3:
            lines.append("Your journal entries this week reflected generally positive emotions.")
        elif avg_sent >= -0.3:
            lines.append("Your journal entries showed a mix of emotional states this week.")
        else:
            lines.append(
                "Your journal entries showed some negative emotional patterns this week. "
                "Writing about what you're experiencing is a healthy step."
            )
    else:
        lines.append("No journal entries this week. Journaling regularly helps build self-awareness.")

    # ── Risk events commentary ────────────────────────────────────────────
    total_risk_pts = sum(risk_points)
    if total_risk_pts == 0:
        lines.append("No significant distress signals were detected in your interactions this week.")
    elif total_risk_pts < 60:
        lines.append(
            f"Moderate distress signals ({total_risk_pts} points) were noted. "
            "Consider trying a breathing exercise or speaking with someone you trust."
        )
    else:
        lines.append(
            "Significant distress signals were detected this week. "
            "Please consider reaching out to one of the professionals in the Therapist Directory."
        )

    # ── Physiological channel note ────────────────────────────────────────
    if not has_physiological:
        lines.append(
            "No voice or video check-ins were recorded this week. "
            "Try a quick video check-in — it helps build a more complete picture of your wellbeing."
        )

    # ── MHI score ─────────────────────────────────────────────────────────
    lines.append(
        f"Your Mental Health Index (MHI) this week is {mhi:.2f} / 1.00 "
        f"({prediction_label}). "
        "A higher score means better overall stability."
    )

    # ── Crisis closing ────────────────────────────────────────────────────
    if is_crisis:
        lines.append(
            "⚠ Important: Your scores this week indicate a high level of distress. "
            "Please reach out to a crisis line or therapist as soon as possible — "
            "you do not have to face this alone."
        )

    return " ".join(lines)


# ── Public interface ───────────────────────────────────────────────────────────

async def get_or_generate_weekly_report(
    db: AsyncSession,
    user_id: UUID,
) -> LateFusionReport:
    """
    Return the current week's Late Fusion report, generating (or regenerating) it.

    Window:  Monday 00:00 → Sunday 23:59 UTC of the current ISO week.
    If the week is not yet complete, uses data from Monday → today.

    Caching policy:
      - Completed weeks (today > Sunday): cached permanently. Subsequent calls
        return the same report — the week is over, no new data can arrive.
      - In-progress weeks (today ≤ Sunday): ALWAYS regenerated. Any stale
        report for the current window is deleted before regeneration so that
        mood logs, journal entries, and chat messages logged today are
        immediately reflected in the next GET /reports/weekly call.

    Flow:
      1. Define the 7-day window.
      2. If week complete, return cached report (if exists).
      3. If week in progress, delete any stale cached report.
      4. Collect all data channels from DB.
      5. Normalise each channel to a 0-1 risk score.
      6. Apply weighted late fusion (PRD §7.3) → composite_risk.
      7. Compute MHI (PRD §7.2) from accumulated risk_log points.
      8. Build qualitative narrative.
      9. Persist and return LateFusionReport.
    """
    # 1. Window
    today      = date.today()
    monday     = today - timedelta(days=today.weekday())
    sunday     = monday + timedelta(days=6)
    period_end = min(today, sunday)

    week_is_complete = today > sunday

    # 2. Return cached report only if the week is fully over
    if week_is_complete:
        existing = await _get_existing_report(db, user_id, monday, period_end)
        if existing:
            return existing

    # 3. In-progress week: delete stale report so new data is reflected
    if not week_is_complete:
        stale = await _get_existing_report(db, user_id, monday, period_end)
        if stale:
            await db.delete(stale)
            await db.flush()

    # 4. Collect data channels
    mood_scores      = await _collect_mood_scores(db, user_id, monday, period_end)
    sentiment_scores = await _collect_journal_sentiments(db, user_id, monday, period_end)
    risk_points      = await _collect_risk_points(db, user_id, monday, period_end)
    ai_analyses      = await _collect_ai_analyses(db, user_id, monday, period_end)

    # 5. Normalise each channel to 0-1 risk
    subjective_risk    = (
        _normalise_mood(mood_scores) * 0.5 +
        _normalise_sentiment(sentiment_scores) * 0.5
    )
    cognitive_risk     = _normalise_text_analysis(ai_analyses)
    physiological_risk = _normalise_physiological(ai_analyses)   # None if no media

    # 6. Weighted late fusion (PRD §7.3)
    composite_risk = _fuse_channels(subjective_risk, cognitive_risk, physiological_risk)

    # 7. MHI from accumulated risk_log points (PRD §7.2)
    days_in_window   = (period_end - monday).days + 1
    total_risk_pts   = sum(risk_points)
    avg_daily_pts    = total_risk_pts / days_in_window
    mhi              = _calculate_mhi(avg_daily_pts)

    # 8. Qualitative narrative
    prediction_label  = _get_prediction_label(mhi)
    is_crisis_flagged = prediction_label == "Crisis" or total_risk_pts >= settings.RISK_SEVERE_THRESHOLD

    qualitative_report = _build_qualitative_report(
        mhi=mhi,
        prediction_label=prediction_label,
        mood_scores=mood_scores,
        sentiment_scores=sentiment_scores,
        risk_points=risk_points,
        has_physiological=physiological_risk is not None,
        is_crisis=is_crisis_flagged,
    )

    # 9. Persist
    report = LateFusionReport(
        user_id=user_id,
        report_period_start=monday,
        report_period_end=period_end,
        prediction_label=prediction_label,
        qualitative_report=qualitative_report,
        is_crisis_flagged=is_crisis_flagged,
        numerical_health_index=mhi,
        fusion_algorithm_version=settings.FUSION_MODEL_VERSION,
    )
    db.add(report)
    await db.flush()

    return report


async def get_therapists(db: AsyncSession) -> list[Therapist]:
    """
    Return the full therapist directory.
    Emergency contacts (is_emergency_contact=True) are sorted first —
    they appear at the top of the Severe Risk screen (PRD §3.2).
    """
    result = await db.execute(
        select(Therapist).order_by(
            Therapist.is_emergency_contact.desc(),
            Therapist.name.asc(),
        )
    )
    return list(result.scalars().all())