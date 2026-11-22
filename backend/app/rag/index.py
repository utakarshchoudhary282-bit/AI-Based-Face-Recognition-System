"""FAISS vector index over the policy chunks: 'find the 4 chunks closest to this question'."""
from langchain_community.vectorstores import FAISS

from ..config import settings
from .documents import load_policy_chunks
from .embeddings import TfidfEmbeddings


class PolicyIndex:
    def __init__(self):
        self.store = None

    def build(self):
        chunks = load_policy_chunks()
        emb = TfidfEmbeddings().fit([c.page_content for c in chunks])
        self.store = FAISS.from_documents(chunks, emb)
        self.store.save_local(str(settings.INDEX_DIR))
        emb.save(settings.INDEX_DIR)
        return len(chunks)

    def ensure(self):
        if self.store is not None:
            return
        if (settings.INDEX_DIR / "index.faiss").exists():
            self.store = FAISS.load_local(str(settings.INDEX_DIR), TfidfEmbeddings.load(settings.INDEX_DIR),
                                          allow_dangerous_deserialization=True)   # our own file
        else:
            self.build()

    def search(self, question: str, k: int = settings.TOP_K):
        """Return [(chunk, similarity 0-1)], best first."""
        self.ensure()
        hits = self.store.similarity_search_with_score(question, k=k)
        # FAISS gives squared distance; for length-1 vectors, similarity = 1 - distance / 2
        return [(doc, round(1 - float(dist) / 2, 3)) for doc, dist in hits]


policy_index = PolicyIndex()
