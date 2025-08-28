# backend/rag/index.py
import os
from typing import List, Dict, Tuple
from backend.settings import CACHE_DIR
from backend.utils.text_chunk import split_text
from backend.utils.dedupe import chunk_hash
from backend.services.gemini import embed_texts
from backend.store.vector_store import VectorStore
import os

EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "8"))

def build_or_update_index(docs: List[Dict[str, str]]) -> Tuple[VectorStore, int]:
    index_path = os.path.join(CACHE_DIR, "index.faiss")
    meta_path  = os.path.join(CACHE_DIR, "meta.json")

    dim = len(embed_texts("probe dim"))  # single call -> safe
    vs = VectorStore(index_path, meta_path, dim)
    vs.load()

    existing_hashes = {m.get("hash") for m in (vs.meta or []) if isinstance(m, dict) and m.get("hash")}
    seen_hashes: set = set()

    vectors, metas = [], []

    for d in docs:
        chunks = split_text(d["text"])
        to_embed, to_meta = [], []

        for ch in chunks:
            h = chunk_hash(ch)
            if h in existing_hashes or h in seen_hashes:
                continue
            seen_hashes.add(h)
            to_embed.append(ch)
            to_meta.append({
                "doc_id": d["doc_id"],
                "source_path": d["source_path"],
                "hash": h,
                "text": ch
            })

        # ---- NEW: embed in batches ----
        for i in range(0, len(to_embed), EMBED_BATCH_SIZE):
            batch_texts = to_embed[i:i + EMBED_BATCH_SIZE]
            batch_meta  = to_meta[i:i + EMBED_BATCH_SIZE]
            if not batch_texts:
                continue
            embs = embed_texts(batch_texts)     # returns list[vectors]
            vectors.extend(embs)
            metas.extend(batch_meta)

    if vectors:
        vs.add(vectors, metas)
        vs.save()

    return vs, dim
