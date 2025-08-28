# DocuChat — Summarize and Ask

A production-ready Streamlit app that:

- **Summarizes** PDFs/DOCX/TXT/MD into a clean **Summary** + **Key Points**  
- **Indexes** documents into a **FAISS** vector store for retrieval  
- **Chats like ChatGPT** (general questions) **and** answers grounded in your docs  
- Supports **voice input** (🎙️ mic to text) and **downloadable summaries**  
- Runs **locally or in Docker/Compose**, with a cloud-friendly **no-upload** mode

---

## ✨ Features

- **Three chat modes**
  - **Auto (smart)** – Uses your docs when relevant; otherwise acts as a general LLM
  - **Docs-only** – Answers strictly from your indexed documents
  - **General LLM** – Ignores docs; general assistant
- **Document scope** – Restrict Q&A to **All documents** or **Selected documents**
- **Summaries** – Per-document Summary & Key Points (download per file or **download all**)
- **Quality RAG pipeline**
  - Header-aware **chunking** with overlap
  - **MMR reranking** (relevance + diversity)
  - **Duplicate protection** via chunk hashing (no re-embedding repeats)
- **Voice input** – Single mic button (streamlit-mic-recorder) → Whisper STT → prefilled chat box
- **Streaming answers** (when the model supports streaming)
- **Two UIs**
  - **Upload UI** (good for desktop/testing)
  - **No-upload server mode** (cloud: auto-load from `data/uploads/`)

---

## 🧱 Tech Stack

- **Frontend:** Streamlit  
- **LLM:** Google Gemini (configurable models)  
- **Embeddings:** Gemini `text-embedding-004` (local model swappable later)  
- **Vector DB:** FAISS (on disk)  
- **OCR:** Tesseract + pdf2image (only when needed)  
- **Audio:** streamlit-mic-recorder + faster-whisper (STT)  
- **Container:** Docker / Docker Compose

---

## 📦 Project Structure

# DocuChat — Summarize and Ask

A production-ready Streamlit app that:

- **Summarizes** PDFs/DOCX/TXT/MD into a clean **Summary** + **Key Points**  
- **Indexes** documents into a **FAISS** vector store for retrieval  
- **Chats like ChatGPT** (general questions) **and** answers grounded in your docs  
- Supports **voice input** (🎙️ mic to text) and **downloadable summaries**  
- Runs **locally or in Docker/Compose**, with a cloud-friendly **no-upload** mode

---

## ✨ Features

- **Three chat modes**
  - **Auto (smart)** – Uses your docs when relevant; otherwise acts as a general LLM
  - **Docs-only** – Answers strictly from your indexed documents
  - **General LLM** – Ignores docs; general assistant
- **Document scope** – Restrict Q&A to **All documents** or **Selected documents**
- **Summaries** – Per-document Summary & Key Points (download per file or **download all**)
- **Quality RAG pipeline**
  - Header-aware **chunking** with overlap
  - **MMR reranking** (relevance + diversity)
  - **Duplicate protection** via chunk hashing (no re-embedding repeats)
- **Voice input** – Single mic button (streamlit-mic-recorder) → Whisper STT → prefilled chat box
- **Streaming answers** (when the model supports streaming)
- **Two UIs**
  - **Upload UI** (good for desktop/testing)
  - **No-upload server mode** (cloud: auto-load from `data/uploads/`)

---

## 🧱 Tech Stack

- **Frontend:** Streamlit  
- **LLM:** Google Gemini (configurable models)  
- **Embeddings:** Gemini `text-embedding-004` (local model swappable later)  
- **Vector DB:** FAISS (on disk)  
- **OCR:** Tesseract + pdf2image (only when needed)  
- **Audio:** streamlit-mic-recorder + faster-whisper (STT)  
- **Container:** Docker / Docker Compose

---

## 📦 Project Structure

# DocuChat — Summarize and Ask

A production-ready Streamlit app that:

- **Summarizes** PDFs/DOCX/TXT/MD into a clean **Summary** + **Key Points**  
- **Indexes** documents into a **FAISS** vector store for retrieval  
- **Chats like ChatGPT** (general questions) **and** answers grounded in your docs  
- Supports **voice input** (🎙️ mic to text) and **downloadable summaries**  
- Runs **locally or in Docker/Compose**, with a cloud-friendly **no-upload** mode

---

## ✨ Features

- **Three chat modes**
  - **Auto (smart)** – Uses your docs when relevant; otherwise acts as a general LLM
  - **Docs-only** – Answers strictly from your indexed documents
  - **General LLM** – Ignores docs; general assistant
- **Document scope** – Restrict Q&A to **All documents** or **Selected documents**
- **Summaries** – Per-document Summary & Key Points (download per file or **download all**)
- **Quality RAG pipeline**
  - Header-aware **chunking** with overlap
  - **MMR reranking** (relevance + diversity)
  - **Duplicate protection** via chunk hashing (no re-embedding repeats)
- **Voice input** – Single mic button (streamlit-mic-recorder) → Whisper STT → prefilled chat box
- **Streaming answers** (when the model supports streaming)
- **Two UIs**
  - **Upload UI** (good for desktop/testing)
  - **No-upload server mode** (cloud: auto-load from `data/uploads/`)

---

## 🧱 Tech Stack

- **Frontend:** Streamlit  
- **LLM:** Google Gemini (configurable models)  
- **Embeddings:** Gemini `text-embedding-004` (local model swappable later)  
- **Vector DB:** FAISS (on disk)  
- **OCR:** Tesseract + pdf2image (only when needed)  
- **Audio:** streamlit-mic-recorder + faster-whisper (STT)  
- **Container:** Docker / Docker Compose

---

## 📦 Project Structure

document-classification-chatbot/
├─ app.py # Streamlit app (Upload UI or No-Upload variant)
├─ backend/
│ ├─ settings.py # Paths & config (UPLOAD_DIR, CACHE_DIR, defaults)
│ ├─ services/
│ │ └─ gemini.py # Chat/stream/summarize/embeddings (retry + throttle)
│ ├─ rag/
│ │ ├─ index.py # Build/update FAISS index, dedupe, chunk
│ │ ├─ qa.py # RAG logic, prompts, context builder
│ │ └─ rerank.py # MMR reranking
│ ├─ store/
│ │ ├─ vector_store.py # FAISS wrapper (add/search/save/load)
│ │ └─ cache.py # Small JSON cache helpers
│ └─ utils/
│ ├─ doc_loader.py # PDF/DOCX/TXT/MD reader (+ optional OCR)
│ ├─ text_chunk.py # Header-aware chunking with overlap
│ ├─ dedupe.py # Chunk hashing
│ └─ audio.py # Whisper-based speech-to-text
├─ data/
│ ├─ uploads/ # Documents (user uploads or server-mounted)
│ └─ cache/ # FAISS index + metadata + summaries cache
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .dockerignore
└─ .env.example



---

## ⚙️ Environment Variables (`.env`)

Create a `.env` (do **not** commit real keys):

``env
# Required
GOOGLE_API_KEY=YOUR_REAL_KEY

# Models
CHAT_MODEL=gemini-1.5-flash          # lighter/faster than -pro
EMBED_MODEL=text-embedding-004

# Throttle / Retry for Gemini (prevents 429 rate limits)
GENAI_MAX_QPS=0.8                    # requests/sec
GENAI_MAX_RETRIES=5
GENAI_BACKOFF=1.0                    # seconds (exponential)

# Embedding size/batching (avoid ~36kB payload limit)
EMBED_MAX_BYTES=30000
EMBED_BATCH_SIZE=8

# Chunking (fewer/bigger chunks = faster indexing)
CHUNK_MAX_CHARS=2200
CHUNK_OVERLAP=120

# Summaries (faster indexing if false)
SUMMARIZE_ON_INDEX=false             # compute on demand in UI

# OCR behavior for PDFs
OCR_MODE=auto                        # auto | off | force

# Streamlit UX
ENABLE_VOICE=true
MIN_FILES=1
RAG_K=5

# 1) Install Python deps
pip install -r requirements.txt

# 2) Copy env and add your key
cp .env.example .env
# edit .env and set GOOGLE_API_KEY

# 3) Start the app
python -m streamlit run app.py

# Open:
# http://localhost:8501


Upload UI: Drag files → Process & Index
No-upload mode: Place files under data/uploads/, click Re-index in the sidebar (or auto-index on start if using the no-upload app)



Docker
A) Build & run (CLI)
docker build -t docuchat:latest .
docker run --name docuchat -p 8501:8501 \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  docuchat:latest
# http://localhost:8501
B) Compose (recommended)
docker compose up -d --build
# http://localhost:8501
If 8501 is taken, change to 8502:8501 in docker-compose.yml.
Rebuild after code changes
docker compose down
docker compose up -d --build
# or, plain docker:
docker rm -f docuchat
docker build -t docuchat:latest .
docker run --name docuchat -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" docuchat:latest

How It Works (Pipeline)
Ingest
doc_loader.py extracts text from PDF/DOCX/TXT/MD. If none found and OCR_MODE=auto|force, it runs OCR (pdf2image + Tesseract).
Chunk
text_chunk.py makes header-aware chunks with overlap (CHUNK_MAX_CHARS, CHUNK_OVERLAP).
Embed & Index
services/gemini.py embeds each chunk (per-item calls, truncated to EMBED_MAX_BYTES, with throttle/retry).
FAISS index + meta.json saved under data/cache/.
Summarize
Hierarchical map-reduce summarization (chunk summaries → reduced final summary).
If SUMMARIZE_ON_INDEX=false, summaries compute lazily when first viewed.
Chat
User asks (typed or mic → STT).
Auto (smart): Embed question → wide FAISS search → MMR rerank → if relevant, answer with context; else general LLM.
Docs-only / General LLM act as named.
Document scope filter (All / Selected) applied before rerank.
Answers can stream.
⚡ Performance Tips
Fewer chunks → faster indexing: raise CHUNK_MAX_CHARS, lower CHUNK_OVERLAP.
Skip summary at index time: SUMMARIZE_ON_INDEX=false (compute on demand).
Avoid OCR unless required: OCR_MODE=off.
Prevent 429 pauses: keep GENAI_MAX_QPS ≤ 1, retries enabled.
Docker resources: allocate more CPUs/RAM in Docker Desktop.
Advanced: switch embeddings to a local model (e.g., sentence-transformers/all-MiniLM-L6-v2) for 10–50× faster indexing and no rate limits.
🧰 Troubleshooting
Port already in use
Bind for 0.0.0.0:8501 failed → stop the old container or map a new host port:
docker stop docuchat && docker rm docuchat
# or use 8502:8501 in compose
429 ResourceExhausted (rate limits)
We throttle + retry automatically. Use CHAT_MODEL=gemini-1.5-flash, lower GENAI_MAX_QPS.
Summaries fall back to a local naive summary so the UI keeps working.
400 payload size exceeds limit (~36kB)
We truncate per-chunk and embed items individually.
If you still see it, reduce CHUNK_MAX_CHARS.
Mic not visible
ENABLE_VOICE=true and allow browser mic permission.
Index corrupted / want a fresh start
Delete data/cache/ (or click Clear Index in the Upload UI) and re-index.
👥 Share with Your Team
Push to Docker Hub
docker tag docuchat:latest <your_dockerhub_username>/docuchat:0.1.0
docker login
docker push <your_dockerhub_username>/docuchat:0.1.0
Teammate runs
echo "GOOGLE_API_KEY=CHANGE_ME" > .env
docker run -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" \
  <your_dockerhub_username>/docuchat:0.1.0
No registry? Send a tarball
docker save docuchat:latest -o docuchat.tar
# teammate:
docker load -i docuchat.tar
🧭 Roadmap (optional)
Local embeddings as a config switch (EMBED_PROVIDER=local|gemini)
Hybrid search (BM25 + vectors with RRF)
Source viewer below answers (show retrieved snippets)
Persistent vector DB (Qdrant/pgvector) for multi-user scale
Auth (SAML/OIDC) and per-team indices
📝 License
MIT (or your preferred license). Add a LICENSE file if you plan to open-source.
🙌 Credits
Google Gemini API
Streamlit
FAISS
Tesseract / pdf2image
faster-whisper / gTTS
✅ One-liner run (Docker)
docker run --name docuchat -p 8501:8501 \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  docuchat:latest
# http://localhost:8501


