"""Step 4 + 5: the classifier and the UNKNOWN rule.

Training:   every saved face -> SFace embedding -> logistic regression (which person?).
Evaluation: 5-fold cross-validation, so every photo is tested once by a model that never saw it.
Prediction: the classifier proposes a person; the face must also have cosine similarity
            >= SIMILARITY_THRESHOLD with at least one enrolled photo of that person,
            otherwise the answer is UNKNOWN (a stranger is not given someone's name).
"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from ..config import settings
from .embedder import embed, embed_many

MODEL_PATH = settings.MODEL_DIR / "face_classifier.joblib"
METRICS_PATH = settings.MODEL_DIR / "metrics.json"


def train(images, labels) -> dict:
    counts = {p: labels.count(p) for p in sorted(set(labels))}
    people = [p for p, n in counts.items() if n >= settings.MIN_IMAGES_PER_PERSON]
    if len(people) < 2:
        raise ValueError(f"Need 2+ people with {settings.MIN_IMAGES_PER_PERSON}+ photos each. Now: {counts}")
    keep = [i for i, p in enumerate(labels) if p in people]
    X = embed_many([images[i] for i in keep])                     # N x 128
    y = np.array([people.index(labels[i]) for i in keep])

    # Honest scores: 5-fold cross-validation
    folds = min(5, int(np.bincount(y).min()))
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    y_pred = cross_val_predict(LogisticRegression(C=10, max_iter=3000), X, y, cv=cv)
    precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average="macro", zero_division=0)
    per_person = precision_recall_fscore_support(y, y_pred, labels=range(len(people)), zero_division=0)

    # Final model on all photos; keep every embedding for the similarity check
    clf = LogisticRegression(C=10, max_iter=3000).fit(X, y)
    joblib.dump({"classifier": clf, "people": people, "embeddings": X, "owners": y}, MODEL_PATH)

    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "people": people,
        "skipped_people": [p for p in counts if p not in people],
        "num_images": len(y),
        "folds": folds,
        "accuracy": round(float(accuracy_score(y, y_pred)), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "per_person": [{"person": p, "precision": round(float(per_person[0][i]), 2),
                        "recall": round(float(per_person[1][i]), 2), "f1": round(float(per_person[2][i]), 2),
                        "photos": int(per_person[3][i])} for i, p in enumerate(people)],
        "confusion_matrix": confusion_matrix(y, y_pred, labels=range(len(people))).tolist(),
        "threshold": settings.SIMILARITY_THRESHOLD,
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


class FaceModel:
    def __init__(self, saved: dict):
        self.clf = saved["classifier"]
        self.people = saved["people"]
        self.embeddings = saved["embeddings"]
        self.owners = saved["owners"]

    def predict(self, face: np.ndarray, top_k: int = 3) -> list[dict]:
        """Top 3 guesses, each with the classifier probability and the face similarity."""
        e = embed(face)
        probs = self.clf.predict_proba([e])[0]
        sims = self.embeddings @ e                       # cosine similarity with every enrolled photo
        best = np.argsort(probs)[::-1][:top_k]
        return [{"label": self.people[i], "probability": round(float(probs[i]), 4),
                 "similarity": round(float(sims[self.owners == i].max()), 4)} for i in best]


def load():
    return FaceModel(joblib.load(MODEL_PATH)) if MODEL_PATH.exists() else None


def load_metrics():
    return json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else None
