"""Text -> vector with TF-IDF (scikit-learn).

TF-IDF gives each word a weight: high if the word appears often in this chunk but rarely in
the other chunks. It needs no model download and works well for policy text full of exact
terms like 'L4', 'Unknown' or '90 days'."""
import joblib
import numpy as np
from langchain_core.embeddings import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer


class TfidfEmbeddings(Embeddings):
    def __init__(self, vectorizer=None):
        self.vectorizer = vectorizer

    def fit(self, texts):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english").fit(texts)
        return self

    def _vectors(self, texts):
        m = self.vectorizer.transform(texts).toarray().astype("float32")
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        return (m / np.where(norms == 0, 1, norms)).tolist()     # length 1 -> distance works like cosine

    def embed_documents(self, texts):
        return self._vectors(texts)

    def embed_query(self, text):
        return self._vectors([text])[0]

    def save(self, folder):
        joblib.dump(self.vectorizer, folder / "tfidf.joblib")

    @classmethod
    def load(cls, folder):
        return cls(joblib.load(folder / "tfidf.joblib"))
