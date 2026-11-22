"""Keeps the trained model in memory and runs training in the background."""
import threading
import traceback

from ..config import settings
from . import sface_model
from .dataset import load_training_set


class FaceService:
    def __init__(self):
        self.model = sface_model.load()
        self.status = {"state": "idle", "message": ""}

    @property
    def ready(self) -> bool:
        return self.model is not None

    def predict(self, face):
        if self.model is None:
            raise RuntimeError("No trained model yet.")
        return self.model.predict(face)

    @staticmethod
    def decide(top) -> str:
        """MATCH only if the best guess is also similar enough to that person's photos."""
        return "MATCH" if top and top[0]["similarity"] >= settings.SIMILARITY_THRESHOLD else "UNKNOWN"

    def start_training(self):
        if self.status["state"] == "running":
            raise RuntimeError("Training is already running.")
        self.status = {"state": "running", "message": "Computing face embeddings..."}
        threading.Thread(target=self._train, daemon=True).start()

    def _train(self):
        try:
            images, labels = load_training_set()
            m = sface_model.train(images, labels)
            self.model = sface_model.load()               # use the new model straight away
            msg = (f"Trained on {m['num_images']} photos of {len(m['people'])} people. "
                   f"Accuracy {m['accuracy']:.1%}, F1 {m['f1']:.2f} ({m['folds']}-fold cross-validation).")
            if m["skipped_people"]:
                msg += f" Skipped (fewer than 5 photos): {', '.join(m['skipped_people'])}."
            self.status = {"state": "done", "message": msg}
        except Exception as exc:
            traceback.print_exc()
            self.status = {"state": "failed", "message": str(exc)}


face_service = FaceService()
