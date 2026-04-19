"""
FAISS Vector Store
===================
Manages per-website FAISS indexes for similarity search.
"""

import os
import pickle
import logging
from typing import List, Dict, Optional
import numpy as np
import faiss

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-backed vector store with metadata."""

    def __init__(self, website_id: int):
        self.website_id = website_id
        self.dimension = settings.EMBEDDING_DIM
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        self._index_dir = os.path.join(settings.FAISS_INDEX_DIR, str(website_id))
        self._index_path = os.path.join(self._index_dir, "index.faiss")
        self._meta_path = os.path.join(self._index_dir, "metadata.pkl")

    def _ensure_dir(self):
        os.makedirs(self._index_dir, exist_ok=True)

    def create_index(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []

    def add_embeddings(self, embedded_chunks: List[Dict]):
        if self.index is None:
            self.create_index()
        vectors = np.array([c["embedding"] for c in embedded_chunks], dtype=np.float32)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        for chunk in embedded_chunks:
            self.metadata.append({"text": chunk["text"], "url": chunk["url"]})
        logger.info(f"Added {len(embedded_chunks)} vectors (total: {self.index.ntotal})")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict]:
        if self.index is None or self.index.ntotal == 0:
            return []
        query = query_vector.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({"text": self.metadata[idx]["text"], "url": self.metadata[idx]["url"], "score": float(score)})
        return results

    def save(self):
        self._ensure_dir()
        faiss.write_index(self.index, self._index_path)
        with open(self._meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self) -> bool:
        if not os.path.exists(self._index_path):
            return False
        self.index = faiss.read_index(self._index_path)
        with open(self._meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        return True

    def delete(self):
        import shutil
        if os.path.exists(self._index_dir):
            shutil.rmtree(self._index_dir)
