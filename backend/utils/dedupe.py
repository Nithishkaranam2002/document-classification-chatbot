# backend/utils/dedupe.py
import hashlib, re

def normalize_text(t: str) -> str:
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t

def chunk_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def file_hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
