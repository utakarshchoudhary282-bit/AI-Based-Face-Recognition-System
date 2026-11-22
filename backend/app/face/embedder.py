"""Step 3: turn an aligned face into 128 numbers (an embedding) with SFace.

SFace is a face-recognition CNN that was already trained on millions of faces (transfer
learning: we reuse it, we don't retrain it). Photos of the same person give embeddings that
point in almost the same direction, so we can compare faces with cosine similarity.
"""
import threading
import urllib.request

import cv2
import numpy as np

from .detector import MODELS_DIR

SFACE_PATH = MODELS_DIR / "face_recognition_sface_2021dec.onnx"
SFACE_URL = ("https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/"
             "face_recognition_sface/face_recognition_sface_2021dec.onnx")
_model = None
_lock = threading.Lock()


def ensure_model():
    """Download the 38 MB SFace file once if it is missing."""
    if not SFACE_PATH.exists():
        print("Downloading the SFace face model (38 MB, one time only)...")
        urllib.request.urlretrieve(SFACE_URL, SFACE_PATH)


def _sface():
    global _model
    if _model is None:
        ensure_model()
        _model = cv2.FaceRecognizerSF.create(str(SFACE_PATH), "")
    return _model


def align(rgb: np.ndarray, yunet_row) -> np.ndarray:
    """Rotate and scale the face using YuNet's landmarks -> 112x112 RGB."""
    with _lock:
        aligned = _sface().alignCrop(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), yunet_row)
    return cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB)


def embed(face: np.ndarray) -> np.ndarray:
    """112x112 RGB face -> 128 numbers, scaled to length 1."""
    with _lock:
        vec = _sface().feature(cv2.cvtColor(face, cv2.COLOR_RGB2BGR)).flatten()
    return vec / np.linalg.norm(vec)


def embed_many(faces) -> np.ndarray:
    return np.stack([embed(f) for f in faces])
