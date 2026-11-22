import io
import os
import tempfile

import pytest
from PIL import Image

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="portal_test_")   # throw-away data folder
os.environ["GROQ_API_KEY"] = ""                                    # no LLM in tests

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def jpg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def face_photo() -> Image.Image:
    from skimage import data          # free sample photo with one clear face
    return Image.fromarray(data.astronaut())


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin(client):
    token = client.post("/api/auth/login", data={"username": "admin", "password": "Admin@123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
