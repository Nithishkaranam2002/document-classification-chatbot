import os
import faiss
import numpy as np
from backend.store.cache import save_json, load_json

class VectorStore:
    def __init__(self, index_path: str, meta_path: str, dim: int):
        self.index_path = index_path
        self.meta_path  = meta_path
        self.dim = dim
        self.index = None
        self.meta  = []

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.meta  = load_json(self.meta_path, [])
        else:
            self.index = faiss.IndexFlatIP(self.dim)  # cosine via L2-normalize
            self.meta  = []

    def add(self, vectors, metadatas):
        arr = np.array(vectors, dtype="float32")
        faiss.normalize_L2(arr)
        self.index.add(arr)
        self.meta.extend(metadatas)

    def save(self):
        faiss.write_index(self.index, self.index_path)
        save_json(self.meta_path, self.meta)

    def search(self, query_vec, k=5):
        if self.index is None or self.index.ntotal == 0:
            return []
        q = np.array([query_vec], dtype="float32")
        faiss.normalize_L2(q)
        D, I = self.index.search(q, k)
        out = []
        for score, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            out.append((float(score), self.meta[idx]))
        return out
