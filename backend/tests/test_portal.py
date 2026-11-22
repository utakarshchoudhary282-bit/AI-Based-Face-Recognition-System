"""8 basic tests: login, roles, face pipeline, open-set rule, RAG."""
import io
import time
import zipfile

import numpy as np
from PIL import Image, ImageEnhance

from tests.conftest import face_photo, jpg


def test_wrong_password_is_rejected(client):
    assert client.post("/api/auth/login", data={"username": "admin", "password": "nope"}).status_code == 401


def test_pages_need_login(client):
    assert client.get("/api/employees").status_code == 401


def test_security_user_cannot_use_admin_pages(client):
    from app.db import SessionLocal, User
    from app.security import hash_password
    with SessionLocal() as db:
        db.add(User(user_id="guard", full_name="Guard", password_hash=hash_password("Guard@123"), role="security"))
        db.commit()
    token = client.post("/api/auth/login", data={"username": "guard", "password": "Guard@123"}).json()["access_token"]
    assert client.get("/api/employees", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_face_is_found_and_aligned():
    from app.face.detector import extract_face
    face, box = extract_face(jpg(face_photo()))
    assert face.shape == (112, 112, 3) and box is not None
    assert extract_face(jpg(Image.new("RGB", (400, 300), "gray")))[0] is None    # blank image: no face


def test_unknown_rule():
    from app.face.service import FaceService
    assert FaceService.decide([{"label": "a", "probability": 0.9, "similarity": 0.80}]) == "MATCH"
    assert FaceService.decide([{"label": "a", "probability": 0.9, "similarity": 0.20}]) == "UNKNOWN"


def test_enrol_train_and_verify(client, admin):
    # person_a: 12 variations of a real face photo, uploaded as a zip with a person folder
    rng = np.random.default_rng(0)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(12):
            img = ImageEnhance.Brightness(face_photo().rotate(rng.uniform(-8, 8))).enhance(rng.uniform(0.8, 1.2))
            zf.writestr(f"dataset/person_a/{i}.jpg", jpg(img))
    r = client.post("/api/enroll/zip", headers=admin, files={"file": ("d.zip", buf.getvalue(), "application/zip")})
    assert r.json()["people"][0]["saved"] == 12

    # person_b: a second person is needed to train a classifier; use simple stand-in faces
    from app.config import settings
    folder = settings.FACES_DIR / "person_b"
    folder.mkdir(exist_ok=True)
    for i in range(8):
        Image.fromarray(rng.integers(0, 255, (112, 112, 3), dtype=np.uint8)).save(folder / f"{i}.jpg")

    client.post("/api/train", headers=admin)
    while client.get("/api/train/status", headers=admin).json()["state"] == "running":
        time.sleep(0.3)
    assert client.get("/api/train/status", headers=admin).json()["state"] == "done"

    v = client.post("/api/verify", headers=admin, files={"file": ("p.jpg", jpg(face_photo()), "image/jpeg")}).json()
    assert v["result"] == "MATCH" and v["employee"]["label"] == "person_a"


def test_rag_finds_the_right_policy(client):
    from app.rag.index import policy_index
    hits = policy_index.search("How many sick leave days do we get?")
    assert "Leave" in hits[0][0].metadata["title"]


def test_assistant_answers_with_sources(client, admin):
    a = client.post("/api/assistant/ask", headers=admin, json={"question": "How long are verification logs kept?"}).json()
    assert a["sources"] and "[S" in a["answer"]
