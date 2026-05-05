"""
Speech processing: Whisper transcription + Wav2Vec2 voice emotion.
"""

import asyncio
import io
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_CHECKPOINT_DIR = Path(__file__).parent / "checkpoints" / "wav2vec2_speech_emotion"
_BASE_MODEL_ID = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

_WHISPER_MODEL = None
_VOICE_CLASSIFIER = None   # HuggingFace pipeline 

# Wav2Vec2 model output labels - our collapsed taxonomy
_WAV2VEC2_COLLAPSE: dict[str, str] = {
    "angry":     "anger",
    "disgust":   "anger",
    "fearful":   "anxiety",
    "happy":     "positive",
    "calm":      "neutral",
    "neutral":   "neutral",
    "surprised": "neutral",
    "sad":       "sadness",
}

WAV2VEC2_LABELS = list(_WAV2VEC2_COLLAPSE.keys())

# Emotions that contribute to physiological distress trigger (> 85%)
DISTRESS_EMOTIONS: set[str] = {"sadness", "anger", "anxiety"}


@dataclass
class VoiceAnalysisResult:
    emotion_label: str
    emotion_score: float
    all_emotions: dict[str, float] = field(default_factory=dict)
    features: dict = field(default_factory=dict)
    is_distressed: bool = False


# Loader 
def load_models(whisper_size: str = "base") -> None:
    global _WHISPER_MODEL, _VOICE_CLASSIFIER
    import torch

    # Whisper — unchanged
    try:
        import whisper as openai_whisper
        logger.info(f"Loading Whisper '{whisper_size}'...")
        _WHISPER_MODEL = openai_whisper.load_model(whisper_size, device="cpu")
        logger.info("Whisper loaded.")
    except Exception as e:
        logger.error(f"Whisper load failed: {e}")

    # Wav2Vec2 — load fine-tuned checkpoint if available, else HuggingFace base
    try:
        from transformers import pipeline

        model_path = str(_CHECKPOINT_DIR) if _CHECKPOINT_DIR.exists() else _BASE_MODEL_ID
        source     = "fine-tuned checkpoint" if _CHECKPOINT_DIR.exists() else "HuggingFace base"
        logger.info(f"Loading Wav2Vec2 from {source}: {model_path}")

        _VOICE_CLASSIFIER = pipeline(
            task="audio-classification",
            model=model_path,
            top_k=None,   # return all label scores
            device=-1
        )
        logger.info("Wav2Vec2 voice classifier loaded.")
    except Exception as e:
        logger.error(f"Wav2Vec2 load failed: {e}. Voice emotion will default to neutral.")


# Transcription — unchanged from CNN-LSTM version 
async def transcribe(audio_bytes: bytes, mime_type: str) -> str:
    if _WHISPER_MODEL is None:
        logger.warning("Whisper not loaded — skipping transcription.")
        return ""

    ext = ".mp4" if "mp4" in mime_type else (".wav" if "wav" in mime_type else ".mp3")

    def _run() -> str:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            return _WHISPER_MODEL.transcribe(tmp, fp16=False)["text"].strip()
        finally:
            os.unlink(tmp)   # delete immediately

    return await asyncio.get_event_loop().run_in_executor(None, _run)


# Librosa features — stored in DB for Late Fusion, unchanged 
def _librosa_features(audio_bytes: bytes) -> dict:
    import librosa, numpy as np

    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)  # 16kHz for Wav2Vec2

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    mel  = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    rms  = librosa.feature.rms(y=y)
    zcr  = librosa.feature.zero_crossing_rate(y)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    try:
        f0 = librosa.yin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"))
        valid_f0 = f0[f0 > 0]
        pitch_mean = float(np.nanmean(valid_f0)) if valid_f0.size else 0.0
        pitch_std  = float(np.nanstd(valid_f0))  if valid_f0.size else 0.0
    except Exception:
        pitch_mean = pitch_std = 0.0

    return {
        "mfcc_mean": mfcc.mean(axis=1).tolist(),
        "mfcc_std": mfcc.std(axis=1).tolist(),
        "mel_mean_db": float(np.mean(librosa.power_to_db(mel))),
        "pitch_mean": pitch_mean,
        "pitch_std": pitch_std,
        "energy_rms": float(np.mean(rms)),
        "zcr_mean": float(np.mean(zcr)),
        "tempo": float(tempo) if not hasattr(tempo, "__len__") else float(tempo[0]),
        "duration_s": float(len(y) / sr),
    }


#  Wav2Vec2 emotion inference 
def _wav2vec2_infer(audio_bytes: bytes) -> tuple[str, float, dict[str, float]]:
    """
    Run Wav2Vec2 audio-classification on raw audio bytes.
    Returns (collapsed_label, score, all_collapsed_scores).
    Defaults to neutral if model not loaded.
    """
    if _VOICE_CLASSIFIER is None:
        return "neutral", 0.0, {"neutral": 1.0}

    try:
        # The HuggingFace audio-classification pipeline can accept raw bytes
        # via a numpy array use soundfile to decode first.
        import numpy as np
        import soundfile as sf

        audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
        if audio_array.ndim > 1:
            audio_array = audio_array.mean(axis=1)   # stereo - mono

        # Resample to 16kHz if needed (Wav2Vec2 requirement)
        if sample_rate != 16000:
            import librosa
            audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=16000)

        raw_results: list[dict] = _VOICE_CLASSIFIER(
            {"array": audio_array.astype(np.float32), "sampling_rate": 16000}
        )

        # Collapse raw labels to our taxonomy and sum scores within same class
        collapsed: dict[str, float] = {}
        for item in raw_results:
            key   = _WAV2VEC2_COLLAPSE.get(item["label"].lower(), "neutral")
            collapsed[key] = collapsed.get(key, 0.0) + item["score"]

        top   = max(collapsed, key=lambda k: collapsed[k])
        return top, round(collapsed[top], 4), {k: round(v, 4) for k, v in collapsed.items()}

    except Exception as e:
        logger.warning(f"Wav2Vec2 inference failed: {e}. Defaulting to neutral.")
        return "neutral", 0.0, {"neutral": 1.0}


#  Public interface
async def extract_voice_features(audio_bytes: bytes) -> VoiceAnalysisResult:
    """Extract Librosa features + Wav2Vec2 emotion. Runs in thread pool."""

    def _run() -> VoiceAnalysisResult:
        feats = _librosa_features(audio_bytes)
        label, score, all_emotions = _wav2vec2_infer(audio_bytes)
        distress_score = sum(v for k, v in all_emotions.items()
            if k in DISTRESS_EMOTIONS)

        # JSONB-safe dict for DB storage
        import json
        jsonb_features = {}
        for k, v in feats.items():
            if isinstance(v, (int, float, str)):
                jsonb_features[k] = v
            elif isinstance(v, list):
                jsonb_features[k] = v  # lists are JSONB-safe
        jsonb_features["all_emotions"] = all_emotions

        return VoiceAnalysisResult(
            emotion_label=label,
            emotion_score=score,
            all_emotions=all_emotions,
            features=jsonb_features,
            is_distressed=distress_score > 0.85,
        )

    return await asyncio.get_event_loop().run_in_executor(None, _run)