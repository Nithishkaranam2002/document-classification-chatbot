import os, time, random, re
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, DeadlineExceeded

API_KEY = os.getenv("GOOGLE_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Models (override via .env)
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")
CHAT_MODEL  = os.getenv("CHAT_MODEL",  "gemini-1.5-flash")  # lighter than 1.5-pro

# Limits / controls
MAX_EMBED_BYTES  = int(os.getenv("EMBED_MAX_BYTES",  "30000"))
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "8"))
MAX_RETRIES      = int(os.getenv("GENAI_MAX_RETRIES","5"))
INITIAL_BACKOFF  = float(os.getenv("GENAI_BACKOFF",  "1.0"))
MAX_QPS          = float(os.getenv("GENAI_MAX_QPS",  "0.8"))  # <= 1 req/sec

_last_call_ts = 0.0
def _throttle():
    """Simple client-side QPS limiter across all Gemini calls."""
    global _last_call_ts
    if MAX_QPS <= 0: 
        return
    min_interval = 1.0 / MAX_QPS
    now = time.monotonic()
    wait = _last_call_ts + min_interval - now
    if wait > 0:
        time.sleep(wait)
    _last_call_ts = time.monotonic()

def _retry_call(fn, *args, **kwargs):
    """Retry with exponential backoff on common transient errors / quota bursts."""
    delay = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        try:
            _throttle()
            return fn(*args, **kwargs)
        except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(delay + random.random()*0.5)
            delay = min(delay * 2, 12)

def _truncate_utf8(s: str, limit: int) -> str:
    b = (s or "").encode("utf-8")
    if len(b) <= limit:
        return s or ""
    return b[:limit].decode("utf-8", errors="ignore")

# ---------- Embeddings ----------
def _embed_one(text: str):
    text = _truncate_utf8(text or "", MAX_EMBED_BYTES - 512)  # headroom
    resp = _retry_call(genai.embed_content, model=EMBED_MODEL, content=text)
    try:
        return resp.embedding.values
    except AttributeError:
        return resp["embedding"]

def embed_texts(text_or_list):
    """str -> vector ; list[str] -> list[vectors] (per-item to avoid size limits)."""
    if isinstance(text_or_list, str):
        return _embed_one(text_or_list)
    out = []
    for t in list(text_or_list or []):
        out.append(_embed_one(t))
    return out

# ---------- Chat ----------
def chat_llm(messages):
    system = "\n".join([m["content"] for m in messages if m["role"] == "system"])
    user   = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    prompt = (system + "\n\n" + user).strip()
    model = genai.GenerativeModel(CHAT_MODEL)
    resp = _retry_call(model.generate_content, prompt)
    return getattr(resp, "text", str(resp))

def chat_llm_stream(messages):
    system = "\n".join([m["content"] for m in messages if m["role"] == "system"])
    user   = "\n".join([m["content"] for m in messages if m["role"] == "user"])
    prompt = (system + "\n\n" + user).strip()
    model = genai.GenerativeModel(CHAT_MODEL)
    # stream call itself retried by letting the first chunk attempt go through a throttle
    _throttle()
    stream = model.generate_content(prompt, stream=True)
    for chunk in stream:
        if getattr(chunk, "text", None):
            yield chunk.text

# ---------- Summaries with graceful fallback ----------
def _naive_summary(text: str, max_words: int = 180) -> str:
    """Local fallback when API is rate limited: first few sentences + quick bullets."""
    text = re.sub(r"\s+", " ", text or "").strip()
    sents = re.split(r"(?<=[.!?])\s+", text)
    head  = " ".join(sents[:5])
    words = head.split()
    if len(words) > max_words:
        head = " ".join(words[:max_words]) + "…"
    # simple bullets: pick distinct long-ish words
    toks = [t.strip(",.;:()[]").lower() for t in text.split()]
    toks = [t for t in toks if 4 <= len(t) <= 18 and t.isalpha()]
    uniq = []
    for t in toks:
        if t not in uniq:
            uniq.append(t)
        if len(uniq) >= 6:
            break
    bullets = "\n".join(f"- {w}" for w in uniq)
    return f"Summary\n\n{head}\n\nKey Points\n{bullets or '- (not available)'}"

def summarize_doc(text: str, max_words: int = 180) -> str:
    prompt = f"Summarize the following document in about {max_words} words and list 3–6 key points.\n\n{text}"
    model = genai.GenerativeModel(CHAT_MODEL)
    try:
        resp = _retry_call(model.generate_content, prompt)
        return getattr(resp, "text", str(resp))
    except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded):
        # Graceful fallback so the UI keeps working
        return _naive_summary(text, max_words)
