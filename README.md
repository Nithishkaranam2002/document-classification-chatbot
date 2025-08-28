DocuChat — Summarize and Ask
A production-ready Streamlit app that:
Summarizes PDFs/DOCX/TXT/MD into a clean summary + key points
Indexes documents into a FAISS vector store for retrieval
Chats like ChatGPT (general questions) and answers grounded in your docs
Supports voice input (mic to text) and downloadable summaries
Runs locally or in Docker/Compose, with optional cloud-friendly “no-upload” mode
✨ Features
Three chat modes
Auto (smart) – uses your docs if relevant; otherwise answers as a general LLM
Docs-only – answers strictly from the uploaded/loaded documents
General LLM – ignores docs; acts like ChatGPT
Document scope – restrict Q&A to All documents or Selected documents
Summaries – per-document Summary & Key Points, with download buttons and download all
RAG quality boosts
Header-aware chunking with overlap
MMR reranking (relevance + diversity)
Duplicate protection via chunk hashing
Voice input – one mic button (Streamlit mic recorder) → STT (Whisper) → prefills the chat box
Streaming answers (when supported by the model)
Two UIs:
Upload UI (good for desktop)
No-upload server mode (cloud deploy: load docs from data/uploads/ only)
🧱 Tech Stack
Frontend: Streamlit
LLM: Google Gemini (configurable models)
Embeddings: Gemini text-embedding-004 (optional: plug a local model later)
Vector DB: FAISS (on disk)
OCR: Tesseract + pdf2image (only when needed)
Audio: streamlit-mic-recorder + faster-whisper + gTTS (optional TTS; we only use STT)
Container: Docker / Docker Compose
