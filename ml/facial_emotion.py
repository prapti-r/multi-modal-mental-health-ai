"""
Production facial emotion classifier for video frames.
"""

import asyncio
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_CHECKPOINT_DIR = Path(__file__).parent / "checkpoints" / "cnn_fer2013"
_CNN_MODEL = None

FER2013_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

# FER2013 raw label
_FER_COLLAPSE: dict[str, str] = {
    "angry":   "anger",
    "disgust": "anger",
    "fear":    "anxiety",
    "happy":   "positive",
    "sad":     "sadness",
    "surprise": "neutral",
    "neutral": "neutral",
}

# Distress emotions for physiological trigger
DISTRESS_EMOTIONS: set[str] = {"anger", "anxiety", "sadness"}
_DISTRESS_THRESHOLD = 0.85   # sum of distress emotion probabilities > 85%


@dataclass
class FacialAnalysisResult:
    dominant_emotion: str
    dominant_score: float
    all_emotions: dict[str, float] = field(default_factory=dict)
    frames_analysed: int = 0
    is_distressed: bool = False   # True - physiological risk pts 


# Loader 
def load_model() -> None:
    """Load CNN-FER2013 checkpoint. Falls back to DeepFace if unavailable."""
    global _CNN_MODEL

    if _CHECKPOINT_DIR.exists():
        try:
            import torch
            _CNN_MODEL = torch.load(
                _CHECKPOINT_DIR / "model.pt", map_location=torch.device('cpu')
            )
            _CNN_MODEL.eval()
            logger.info(f"FER2013 CNN loaded from {_CHECKPOINT_DIR}.")
        except Exception as e:
            logger.error(f"FER2013 CNN load failed: {e}. Will fall back to DeepFace.")
    else:
        logger.warning(
            f"FER2013 checkpoint not found at {_CHECKPOINT_DIR}. "
            "Run ml/training/train_facial.py to generate it. "
            "Falling back to DeepFace for facial emotion."
        )


# CNN inference on a single frame
def _infer_frame_cnn(frame_gray: "np.ndarray") -> dict[str, float] | None:
    try:
        import cv2, numpy as np, torch
        from torchvision import transforms
        from PIL import Image

        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.Lambda(lambda x: x.convert("RGB")),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225]),
        ])

        tensor = transform(frame_gray).unsqueeze(0)  # (1, 3, 224, 224)

        with torch.no_grad():
            probs = torch.softmax(_CNN_MODEL(tensor), dim=-1).squeeze().tolist()

        raw_scores = dict(zip(FER2013_LABELS, probs))
        collapsed: dict[str, float] = {}
        for raw_lbl, score in raw_scores.items():
            key = _FER_COLLAPSE.get(raw_lbl, "neutral")
            collapsed[key] = collapsed.get(key, 0.0) + score
        return collapsed
    except Exception as e:
        logger.debug(f"CNN frame inference failed: {e}")
        return None


def _infer_frame_deepface(frame_bgr: "np.ndarray") -> dict[str, float] | None:
    """Fallback: DeepFace emotion analysis on a single BGR frame."""
    try:
        from deepface import DeepFace
        result = DeepFace.analyze(
            frame_bgr, actions=["emotion"], enforce_detection=False, silent=True
        )
        raw = result[0]["emotion"]   # values are 0-100
        collapsed: dict[str, float] = {}
        for raw_lbl, score in raw.items():
            key = _FER_COLLAPSE.get(raw_lbl.lower(), "neutral")
            collapsed[key] = collapsed.get(key, 0.0) + score / 100.0
        return collapsed
    except Exception as e:
        logger.debug(f"DeepFace frame inference failed: {e}")
        return None


# Video processing 
def _process_video(video_bytes: bytes) -> FacialAnalysisResult:
    """
    Sample frames from a video, detect faces, run emotion classification,
    and average results across all analysed frames.
    """
    import cv2, numpy as np

    use_cnn    = _CNN_MODEL is not None
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(video_bytes)
        tmp_path = f.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        sample_every = max(1, int(fps * 2))   # sample one frame every 2 seconds

        frame_scores: list[dict[str, float]] = []
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_every == 0:
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                if len(faces) > 0:
                    # Use largest detected face
                    x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
                    face_gray   = gray[y:y+h, x:x+w]
                    face_bgr    = frame[y:y+h, x:x+w]

                    scores = (
                        _infer_frame_cnn(face_gray)
                        if use_cnn
                        else _infer_frame_deepface(face_bgr)
                    )
                    if scores:
                        frame_scores.append(scores)

            frame_idx += 1

        cap.release()
    finally:
        os.unlink(tmp_path)   # delete immediately

    if not frame_scores:
        return FacialAnalysisResult(
            dominant_emotion="neutral",
            dominant_score=1.0,
            all_emotions={"neutral": 1.0},
            frames_analysed=0,
        )

    # Average scores across all analysed frames
    all_keys   = set().union(*frame_scores)
    avg_scores = {
        k: round(sum(f.get(k, 0.0) for f in frame_scores) / len(frame_scores), 4)
        for k in all_keys
    }
    dominant   = max(avg_scores, key=lambda k: avg_scores[k])
    distress   = sum(avg_scores.get(k, 0.0) for k in DISTRESS_EMOTIONS)

    return FacialAnalysisResult(
        dominant_emotion=dominant,
        dominant_score=avg_scores[dominant],
        all_emotions=avg_scores,
        frames_analysed=len(frame_scores),
        is_distressed=distress > _DISTRESS_THRESHOLD,
    )


# Public interface 
async def extract_facial_emotions(video_bytes: bytes) -> FacialAnalysisResult:
    """Extract facial emotions from video bytes. Runs in thread pool."""
    return await asyncio.get_event_loop().run_in_executor(
        None, _process_video, video_bytes
    )