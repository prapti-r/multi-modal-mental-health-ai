"""
Orchestrates the full multi-modal analysis pipeline for a single media upload.

"""

from dataclasses import dataclass

from core.config import settings
from core.exceptions import MediaProcessingError, ValidationError
from ml import bert_classifier, facial_emotion, speech_emotion
from ml.bert_classifier import TextAnalysisResult


@dataclass
class MediaAnalysisOutput:
    """Maps 1:1 to AiAnalysisResult columns."""
    transcript: str | None = None
    text_analysis:dict | None = None   # BERT output
    voice_features: dict | None = None   # Librosa + CNN-LSTM output
    facial_emotions: dict | None = None   # FER2013 CNN output
    bert_result: TextAnalysisResult | None = None   # kept for risk evaluation


# Validation 
def validate_upload(filename: str, content_type: str, size_bytes: int) -> None:
    """
    Reject uploads that violate MIME type or size constraints 

    Raises:
        ValidationError: on invalid content type or file too large.
    """
    if content_type not in settings.ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported file type '{content_type}'. "
            f"Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}."
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(
            f"File too large ({size_bytes / 1_048_576:.1f} MB). "
            f"Maximum: {settings.MAX_UPLOAD_SIZE_MB} MB."
        )


# Pipeline 
async def process_media(
    file_bytes: bytes,
    content_type: str,
) -> MediaAnalysisOutput:
    """
    Run the full multi-modal pipeline on in-memory bytes.

    Raises:
        MediaProcessingError: on any analysis failure — caller engages fallback.
    """
    is_video = content_type == "video/mp4"
    is_audio = content_type in ("audio/wav", "audio/mpeg")

    try:
        output = MediaAnalysisOutput()

        # Whisper transcription (audio + video) 
        if is_audio or is_video:
            transcript = await speech_emotion.transcribe(file_bytes, content_type)
            output.transcript = transcript

            # BERT on transcript
            if transcript:
                bert_result = await bert_classifier.classify_text(transcript)
                output.bert_result = bert_result
                output.text_analysis = {
                    "label": bert_result.label,
                    "score": bert_result.score,
                    "raw_label": bert_result.raw_label,
                    "is_crisis": bert_result.is_crisis,
                    "is_deep_hopelessness": bert_result.is_deep_hopelessness,
                    "all_scores": bert_result.all_scores,
                }

        # Librosa + CNN-LSTM voice features
        if is_audio or is_video:
            voice_result = await speech_emotion.extract_voice_features(file_bytes)
            output.voice_features = voice_result.features   # JSONB-safe dict

        # OpenCV + CNN-FER2013 facial emotions (video only) 
        if is_video:
            facial_result          = await facial_emotion.extract_facial_emotions(file_bytes)
            output.facial_emotions = {
                "dominant_emotion": facial_result.dominant_emotion,
                "dominant_score": facial_result.dominant_score,
                "all_emotions": facial_result.all_emotions,
                "frames_analysed": facial_result.frames_analysed,
                "is_distressed": facial_result.is_distressed,
            }

        return output

    except (ValidationError, MediaProcessingError):
        raise
    except Exception as exc:
        raise MediaProcessingError(f"Media pipeline failed: {exc}") from exc


# Physiological distress check 
def check_physiological_distress(output: MediaAnalysisOutput) -> bool:
    """
    Return True if facial OR voice distress intensity exceeds 85%
    """
    # Facial check
    if output.facial_emotions:
        distress_emotions = {"anger", "anxiety", "sadness"}
        all_em = output.facial_emotions.get("all_emotions", {})
        if sum(all_em.get(e, 0.0) for e in distress_emotions) > 0.85:
            return True

    # Voice check — use CNN-LSTM collapsed distress score from voice_features
    if output.voice_features:
        all_em = output.voice_features.get("all_emotions", {})
        distress_emotions = {"sadness", "anger", "anxiety"}
        if sum(all_em.get(e, 0.0) for e in distress_emotions) > 0.85:
            return True

    return False