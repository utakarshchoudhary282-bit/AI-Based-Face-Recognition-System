"""Step 1 + 2: find the face (YuNet) and align it (SFace's alignCrop).

YuNet is a small CNN face detector from the OpenCV model zoo. For each face it returns a box,
a confidence score and 5 landmarks (both eyes, nose tip, both mouth corners). The landmarks are
used to rotate and scale the face to a standard 112x112 image, so the eyes always sit in the
same place. Training photos and verification photos go through this SAME code.
"""
import io
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MODELS_DIR = Path(__file__).resolve().parent / "models"
YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
MIN_SCORE = 0.75        # YuNet confidence needed to count as a face
MIN_FACE_PX = 24        # smaller faces are too blurry to recognise
MAX_SIDE = 1280         # big phone photos are shrunk first

_detector = None
_lock = threading.Lock()


def load_rgb(image_bytes: bytes) -> np.ndarray:
    """Open any common image, fix phone rotation, shrink if huge, return RGB pixels."""
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ValueError("Not a valid image file")
    scale = MAX_SIDE / max(img.size)
    if scale < 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    return np.array(img)


def detect_faces(rgb: np.ndarray):
    """Return YuNet's rows for every face found: [x, y, w, h, 10 landmark values, score]."""
    global _detector
    with _lock:
        if _detector is None:
            _detector = cv2.FaceDetectorYN.create(str(YUNET_PATH), "", (320, 320), MIN_SCORE)
        _detector.setInputSize((rgb.shape[1], rgb.shape[0]))
        _, faces = _detector.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    if faces is None:
        return []
    return [f for f in faces if f[2] >= MIN_FACE_PX and f[3] >= MIN_FACE_PX]


def extract_face(image_bytes: bytes):
    """Largest face in the photo -> (aligned 112x112 RGB face, box). (None, None) if no face."""
    from .embedder import align
    rgb = load_rgb(image_bytes)
    faces = detect_faces(rgb)
    if not faces:
        return None, None
    face = max(faces, key=lambda f: f[2] * f[3])          # largest face = the main person
    box = tuple(int(v) for v in face[:4])
    return align(rgb, face), box


def profile_photo(image_bytes: bytes) -> bytes:
    """A 300x300 JPEG of the face with some background, for the employee card."""
    rgb = load_rgb(image_bytes)
    faces = detect_faces(rgb)
    h, w = rgb.shape[:2]
    if faces:
        x, y, fw, fh = (int(v) for v in max(faces, key=lambda f: f[2] * f[3])[:4])
        side = int(max(fw, fh) * 2.2)
        cx, cy = x + fw // 2, y + fh // 2
    else:
        side, cx, cy = min(h, w), w // 2, h // 2
    x1, y1 = max(0, cx - side // 2), max(0, cy - side // 2)
    crop = rgb[y1:min(h, y1 + side), x1:min(w, x1 + side)]
    buf = io.BytesIO()
    Image.fromarray(cv2.resize(crop, (300, 300))).save(buf, format="JPEG", quality=90)
    return buf.getvalue()
