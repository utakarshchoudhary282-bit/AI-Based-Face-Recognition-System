"""Enrolment: photos uploaded for a person -> aligned faces saved in data/faces/<label>/."""
import io
import re
import uuid
import zipfile
from collections import defaultdict
from pathlib import PurePosixPath

import numpy as np
from PIL import Image

from ..config import settings
from .detector import extract_face, profile_photo

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def make_label(text: str) -> str:
    """'Rohit Kumar' -> 'rohit_kumar' (safe to use as a folder name)."""
    return re.sub(r"[^a-z0-9_]+", "_", text.strip().lower()).strip("_") or "person"


def count_faces(label: str) -> int:
    folder = settings.FACES_DIR / label
    return len(list(folder.glob("*.jpg"))) if folder.exists() else 0


def save_faces(label: str, files: list[tuple[str, bytes]]) -> dict:
    """Detect + align the face in every photo and save it. Photos without a face are skipped."""
    folder = settings.FACES_DIR / label
    folder.mkdir(parents=True, exist_ok=True)
    saved, skipped, first_good = 0, [], None
    for name, data in files:
        try:
            face, _ = extract_face(data)
        except ValueError:
            face = None
        if face is None:
            skipped.append(name)
            continue
        Image.fromarray(face).save(folder / f"{uuid.uuid4().hex[:12]}.jpg", quality=95)
        saved += 1
        first_good = first_good or data
    return {"label": label, "saved": saved, "skipped": skipped,
            "total_faces": count_faces(label), "first_good_image": first_good}


def save_profile_photo(label: str, image_bytes: bytes) -> str:
    path = settings.PHOTOS_DIR / f"{label}.jpg"
    path.write_bytes(profile_photo(image_bytes))
    return str(path)


def read_zip(zip_bytes: bytes) -> dict[str, list[tuple[str, bytes]]]:
    """A zip like 'project 1/udit/a.jpg': the folder holding each photo is the person's label.
    Read in memory, so a strange file name can never write outside our data folder."""
    people = defaultdict(list)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for item in zf.infolist():
            path = PurePosixPath(item.filename.replace("\\", "/"))
            if item.is_dir() or path.suffix.lower() not in IMAGE_EXTS or len(path.parts) < 2:
                continue
            if "__MACOSX" in path.parts:
                continue
            people[make_label(path.parts[-2])].append((path.name, zf.read(item)))
    if not people:
        raise ValueError("No person folders found. Expected: <person_name>/<photo>.jpg")
    return dict(people)


def load_training_set():
    """All saved faces -> (images N x 112 x 112 x 3, labels)."""
    images, labels = [], []
    for person in sorted(p for p in settings.FACES_DIR.iterdir() if p.is_dir()):
        for f in sorted(person.glob("*.jpg")):
            images.append(np.array(Image.open(f).convert("RGB").resize((112, 112))))
            labels.append(person.name)
    return images, labels
