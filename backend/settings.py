import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .env")

DATA_DIR   = "data"
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
CACHE_DIR  = os.path.join(DATA_DIR, "cache")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)

# RAG / chunking
RAG_K          = int(os.getenv("RAG_K", "5"))
CHUNK_TOKENS   = int(os.getenv("CHUNK_TOKENS", "2200"))
OVERLAP_TOKENS = int(os.getenv("OVERLAP_TOKENS", "150"))

# Voice
ENABLE_VOICE = os.getenv("ENABLE_VOICE", "false").lower() == "true"
TTS_ENGINE   = os.getenv("TTS_ENGINE", "gtts")

# NEW: minimum files required to index (default 1)
MIN_FILES = int(os.getenv("MIN_FILES", "1"))
