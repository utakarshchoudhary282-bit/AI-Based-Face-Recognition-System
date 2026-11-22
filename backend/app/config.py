"""All settings in one place. Values come from environment variables or the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    # Folders
    DATA_DIR = Path(os.getenv("DATA_DIR", str(BACKEND_DIR / "data")))
    FACES_DIR = DATA_DIR / "faces"        # one folder of aligned 112x112 faces per employee
    PHOTOS_DIR = DATA_DIR / "photos"      # one profile photo per employee
    MODEL_DIR = DATA_DIR / "model"        # trained classifier + metrics
    INDEX_DIR = DATA_DIR / "rag_index"    # FAISS index of the policy documents
    POLICY_DIR = BACKEND_DIR / "knowledge_base" / "policies"
    DB_URL = f"sqlite:///{DATA_DIR / 'portal.db'}"

    # Login
    JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
    JWT_EXPIRE_MINUTES = 480                                  # 8 hours
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

    # Face recognition
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))  # below this -> UNKNOWN
    MIN_IMAGES_PER_PERSON = 5

    # RAG assistant
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    TOP_K = 4                                                  # chunks given to the LLM


settings = Settings()

for folder in (settings.DATA_DIR, settings.FACES_DIR, settings.PHOTOS_DIR,
               settings.MODEL_DIR, settings.INDEX_DIR):
    folder.mkdir(parents=True, exist_ok=True)
