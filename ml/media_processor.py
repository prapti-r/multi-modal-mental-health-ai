import os
import logging
import subprocess
from dataclasses import dataclass
import whisper
import subprocess

from core.config import settings
from core.exceptions import MediaProcessingError, ValidationError
from ml import bert_classifier, facial_emotion, speech_emotion
from ml.bert_classifier import TextAnalysisResult

logger = logging.getLogger(__name__)

FFMPEG_EXE_PATH = r"C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"
TEMP_DIR = r"C:\backend\temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

whisper_model = whisper.load_model("base")


@dataclass
class MediaAnalysisOutput:
    """Maps 1:1 to AiAnalysisResult columns."""
    transcript:      str | None = None
    text_analysis:   dict | None = None
    voice_features:  dict | None = None
    facial_emotions: dict | None = None
    bert_result:     TextAnalysisResult | None = None


def validate_upload(filename: str, content_type: str, size_bytes: int) -> None:
    """
    Reject uploads that violate MIME type or size constraints.
    Note: chat_service normalises the content_type before calling this,
    so by the time we validate it should already be one of the accepted types.
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

#  helper function to convert the uploaded file into a standard format
def convert_to_standard_format(input_path: str):
    """Converts input to a standard MP4/WAV that ML models can read."""
    # create a temporary output path
    temp_output = input_path + "_converted.mp4"
    
    # Force conversion to standard AAC audio and H264 video
    # -y (overwrite), -loglevel error (quiet)
    cmd = [
        FFMPEG_EXE_PATH, "-i", input_path,
        "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental",
        "-b:a", "128k", "-ar", "16000", "-y", temp_output
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        # Replace the original file with the converted one
        logger.info(f"FFmpeg conversion successful: {temp_output}")
        return temp_output

        logger.info(f"FFmpeg conversion successful: {input_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")


async def process_media(
    uploaded_file_bytes: bytes,
    filename: str,           
    content_type: str,
) -> MediaAnalysisOutput:
    """
    Run the full multi-modal pipeline on in-memory bytes.
    Writes to a temp file, runs Whisper → BERT → Librosa → DeepFace, then cleans up.

    Raises:
        MediaProcessingError: on any analysis failure — caller engages fallback.
    """
    # Accepted after normalisation by chat_service
    is_video = content_type in ["video/mp4", "video/quicktime"]
    is_audio = content_type in ["audio/wav", "audio/mpeg"] # mpeg covers m4a/3gp after normalisation

    file_path = os.path.join(TEMP_DIR, filename)
    logger.info(f"Starting media analysis: {file_path} ({content_type})")

    # Write bytes to disk (Whisper and OpenCV need a file path, not bytes)
    with open(file_path, "wb") as f:
        f.write(uploaded_file_bytes)
    logger.debug(f"File parked at {file_path}")

    try:
        # Verify FFmpeg is available
        ffmpeg_check = subprocess.run(
            [FFMPEG_EXE_PATH, "-version"],
            capture_output=True, text=True
        )
        if ffmpeg_check.returncode != 0:
            raise MediaProcessingError("FFmpeg not available")
        logger.debug(f"FFmpeg OK: {ffmpeg_check.stdout.splitlines()[0]}")

        if is_video or is_audio:
            file_path = convert_to_standard_format(file_path)
            
        output = MediaAnalysisOutput()

        #  Whisper transcription 
        if is_audio or is_video:
            logger.info("Running Whisper transcription...")
            result     = whisper_model.transcribe(file_path)
            transcript = result.get("text", "").strip()
            output.transcript = transcript or None
            logger.info(f"Transcript: {transcript[:80] if transcript else '(empty)'}")

            # BERT on transcript
            if transcript:
                bert_result         = await bert_classifier.classify_text(transcript)
                output.bert_result  = bert_result
                output.text_analysis = {
                    "label":               bert_result.label,
                    "score":               bert_result.score,
                    "raw_label":           bert_result.raw_label,
                    "is_crisis":           bert_result.is_crisis,
                    "is_deep_hopelessness": bert_result.is_deep_hopelessness,
                    "all_scores":          bert_result.all_scores,
                }

        #  Librosa + CNN-LSTM voice features 
        if is_audio or is_video:
            logger.info("Extracting voice features...")
            voice_result         = await speech_emotion.extract_voice_features(file_path)
            output.voice_features = voice_result.features

        #  OpenCV + DeepFace facial emotions (video only) 
        if is_video:
            logger.info("Extracting facial emotions...")
            # FIX: pass file_path (not file_bytes)
            facial_result          = await facial_emotion.extract_facial_emotions(file_path)
            output.facial_emotions = {
                "dominant_emotion": facial_result.dominant_emotion,
                "dominant_score":   facial_result.dominant_score,
                "all_emotions":     facial_result.all_emotions,
                "frames_analysed":  facial_result.frames_analysed,
                "is_distressed":    facial_result.is_distressed,
            }

        return output

    except (ValidationError, MediaProcessingError):
        raise
    except Exception as exc:
        logger.error(f"Pipeline failed for {filename}: {exc}", exc_info=True)
        raise MediaProcessingError(f"Media pipeline failed: {exc}") from exc
    finally:
        # Always clean up temp file — raw bytes must not persist > 10 min (PRD requirement)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Temp file deleted: {file_path}")
        except Exception as cleanup_err:
            logger.warning(f"Could not delete temp file {file_path}: {cleanup_err}")


def check_physiological_distress(output: MediaAnalysisOutput) -> bool:
    """Return True if facial OR voice distress intensity exceeds 85%."""
    distress_emotions = {"anger", "anxiety", "sadness"}

    if output.facial_emotions:
        all_em = output.facial_emotions.get("all_emotions", {})
        if sum(all_em.get(e, 0.0) for e in distress_emotions) > 0.85:
            return True

    if output.voice_features:
        all_em = output.voice_features.get("all_emotions", {})
        if sum(all_em.get(e, 0.0) for e in distress_emotions) > 0.85:
            return True

    return False