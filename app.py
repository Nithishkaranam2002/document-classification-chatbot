import os
import uuid
from typing import List, Tuple
import streamlit as st

from backend.settings import UPLOAD_DIR, CACHE_DIR, ENABLE_VOICE, MIN_FILES
from backend.utils.doc_loader import load_text_from_path
from backend.services.gemini import summarize_doc, chat_llm, embed_texts
try:
    from backend.services.gemini import chat_llm_stream
    HAS_STREAM = True
except Exception:
    HAS_STREAM = False

from backend.rag.index import build_or_update_index
from backend.rag.qa import PROMPT_SYSTEM
from backend.rag.rerank import mmr_rerank
from backend.utils.audio import transcribe_audio_bytes

# Mic recorder (compact)
try:
    from streamlit_mic_recorder import mic_recorder
    MIC_AVAILABLE = True
except Exception:
    MIC_AVAILABLE = False


# -------------------- UI --------------------
st.set_page_config(page_title="DocuChat – Summarize and Ask", layout="wide")
st.title("📄✨ DocuChat – Summarize and Ask")

# -------------------- STATE --------------------
ss = st.session_state
ss.setdefault("docs", {})               # {doc_id: {name,path,text,summary,keys}}
ss.setdefault("vecstore", None)
ss.setdefault("history", [{"role":"system","content":"You are a helpful assistant."}])
ss.setdefault("chat_input", "")
ss.setdefault("_apply_prefill_text", False)
ss.setdefault("_prefill_text", "")
ss.setdefault("_clear_input", False)
ss.setdefault("scope_mode", "All documents")
ss.setdefault("scope_ids", [])          # selected doc_ids for filtering


# -------------------- HELPERS --------------------
def save_uploads(files):
    paths = []
    for f in files:
        dest = os.path.join(UPLOAD_DIR, f.name)
        with open(dest, "wb") as out:
            out.write(f.read())
        paths.append(dest)
    return paths

def parse_summary(text):
    res = summarize_doc(text, max_words=180)
    if "Key Points" in res:
        a, b = res.split("Key Points", 1)
        return a.replace("Summary", "").strip(), "Key Points" + b
    return res, ""

def build_doc_md(name: str, summary: str, keys: str) -> str:
    md = [f"# {name}", ""]
    if summary.strip():
        md += ["## Summary", summary.strip(), ""]
    if keys.strip():
        md += ["## Key Points", keys.strip(), ""]
    return "\n".join(md)

def build_all_md(docs: dict) -> str:
    parts = []
    for info in docs.values():
        parts.append(build_doc_md(info["name"], info["summary"], info["keys"]))
        parts.append("\n---\n")
    return "\n".join(parts).strip()

def _avg_top_sim(hits: List[Tuple[float, dict]], k: int) -> float:
    if not hits: return 0.0
    sims = [float(s) for s, _ in hits[:k]]
    return sum(sims) / max(1, len(sims))

def fetch_context_with_mmr(question: str, k: int = 5, widen: int = 6, allowed_ids: List[str] | None = None):
    """
    Retrieve a wide set from FAISS, optionally filter by allowed doc_ids,
    MMR-rerank to k, and return (context, files, avg_score).
    """
    if ss.vecstore is None or getattr(ss.vecstore, "index", None) is None or ss.vecstore.index.ntotal == 0:
        return "", [], 0.0

    q_emb = embed_texts(question)
    wide_k = max(k * widen, 30)
    pre_hits = ss.vecstore.search(q_emb, k=wide_k) or []

    # Filter to selected docs if provided
    if allowed_ids:
        filtered = [h for h in pre_hits if h[1].get("doc_id") in set(allowed_ids)]
        if len(filtered) < k:
            # try an even wider pull to find enough matches from selected docs
            pre_hits2 = ss.vecstore.search(q_emb, k=wide_k * 3) or []
            extra = [h for h in pre_hits2 if h[1].get("doc_id") in set(allowed_ids)]
            # keep order, avoid duplicates
            seen = set(id(h) for h in filtered)
            filtered += [h for h in extra if id(h) not in seen]
        pre_hits = filtered

    if not pre_hits:
        return "", [], 0.0

    cand_texts = [m["text"] for _, m in pre_hits]
    cand_vecs  = embed_texts(cand_texts)
    order = mmr_rerank(q_emb, cand_texts, cand_vecs, k=k, lambda_mult=0.6)
    hits  = [pre_hits[i] for i in order]
    score = _avg_top_sim(hits, k)

    chunks, files = [], []
    for s, meta in hits[:k]:
        fname = meta.get("source_path", "").split("/")[-1]
        files.append(fname)
        chunks.append(f"[{fname}] {meta.get('text','')}")
    context = "\n\n---\n\n".join(chunks)
    files = list(dict.fromkeys(files))
    return context, files, score

def stream_or_call(messages):
    with st.chat_message("assistant"):
        if HAS_STREAM:
            placeholder, final = st.empty(), ""
            for delta in chat_llm_stream(messages):
                final += delta
                placeholder.markdown(final)
            return final
        text = chat_llm(messages)
        st.markdown(text)
        return text


# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.header("Upload Documents")
    files = st.file_uploader(
        "Upload files (pdf/docx/txt/md)",
        type=["pdf","docx","txt","md"],
        accept_multiple_files=True,
    )
    colA, colB = st.columns(2)
    build_idx = colA.button("Process & Index")
    clear_idx = colB.button("Clear Index")

    st.markdown("### Chat Mode")
    chat_mode = st.radio(
        "How should the bot answer?",
        options=["Auto (smart)", "Docs-only", "General LLM"],
        index=0,
    )

    # 🔽 NEW: Document scope
    st.markdown("### Document scope")
    ss.scope_mode = st.radio(
        "Which documents should answers use?",
        options=["All documents", "Selected documents"],
        index=0,
    )
    if ss.scope_mode == "Selected documents" and ss.docs:
        # map names -> ids for user-friendly selection
        name_to_id = {info["name"]: did for did, info in ss.docs.items()}
        chosen = st.multiselect("Choose documents", list(name_to_id.keys()))
        ss.scope_ids = [name_to_id[n] for n in chosen]
    else:
        ss.scope_ids = []

    # Downloads (quick)
    if ss.docs:
        st.markdown("### Summaries")
        with st.container(border=True):
            st.caption("Quick downloads")
            st.download_button(
                "⬇️ Download all summaries (.md)",
                data=build_all_md(ss.docs),
                file_name="summaries_all.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.divider()
            for did, info in ss.docs.items():
                col1, col2 = st.columns([0.65, 0.35])
                col1.write(f"**{info['name']}**")
                md = build_doc_md(info["name"], info["summary"], info["keys"])
                col2.download_button(
                    "Download",
                    data=md,
                    file_name=f"{os.path.splitext(info['name'])[0]}_summary.md",
                    mime="text/markdown",
                    key=f"dl_{did}",
                    use_container_width=True,
                )

    if clear_idx:
        for fn in os.listdir(CACHE_DIR):
            try: os.remove(os.path.join(CACHE_DIR, fn))
            except Exception: pass
        ss.vecstore = None
        st.success("Index cleared.")


# -------------------- UPLOAD & INDEX --------------------
if files and build_idx:
    if len(files) < MIN_FILES:
        st.error(f"Please upload at least {MIN_FILES} file(s) before indexing.")
    else:
        paths = save_uploads(files)
        for p in paths:
            doc_id = str(uuid.uuid4())[:8]
            try:
                text = load_text_from_path(p)
            except Exception as e:
                st.error(f"Failed to read {os.path.basename(p)}: {e}")
                continue
            summary, keys = parse_summary(text)
            ss.docs[doc_id] = {"name": os.path.basename(p), "path": p, "text": text, "summary": summary, "keys": keys}
        st.success(f"Processed {len(paths)} file(s). Building index…")

        doc_list = [{"doc_id": k, "text": v["text"], "source_path": v["path"]} for k, v in ss.docs.items()]
        if doc_list:
            vs, _ = build_or_update_index(doc_list)
            ss.vecstore = vs
            st.success("Index ready ✅")


# -------------------- SUMMARIES (main) --------------------
if ss.docs:
    st.subheader("Summaries")
    for did, info in ss.docs.items():
        with st.expander(f"🗂 {info['name']}"):
            st.markdown(f"**Summary**\n\n{info['summary']}")
            if info["keys"]:
                st.markdown(f"\n\n**Key Points**\n\n{info['keys']}")


# -------------------- CHAT --------------------
st.header("💬 Chatbot")

# apply flags BEFORE creating input
if ss._apply_prefill_text:
    ss.chat_input = ss._prefill_text or ""
    ss._apply_prefill_text = False
    ss._prefill_text = ""
if ss._clear_input:
    ss.chat_input = ""
    ss._clear_input = False

# row: mic | input | send
c_mic, c_input, c_send = st.columns([0.12, 0.68, 0.20])

# mic → prefill
if ENABLE_VOICE and MIC_AVAILABLE:
    with c_mic:
        rec = mic_recorder(start_prompt="🎙️", stop_prompt="⏹", just_once=True,
                           use_container_width=True, format="wav", key="mic_key")
    if rec and isinstance(rec, dict) and rec.get("bytes"):
        try:
            text = transcribe_audio_bytes(rec["bytes"], language="en")
            if text:
                ss._prefill_text = text
                ss._apply_prefill_text = True
                st.rerun()
        except Exception as e:
            st.toast(f"Transcription failed: {e}", icon="⚠️")
else:
    c_mic.write("")

_ = c_input.text_input("Ask about your docs or anything:", key="chat_input", label_visibility="collapsed")
ask_btn   = c_send.button("Send", use_container_width=True)
clear_btn = st.button("Clear chat")

if clear_btn:
    ss.history = [{"role":"system","content":"You are a helpful assistant."}]
    ss._clear_input = True
    st.rerun()

if ask_btn:
    question = (ss.chat_input or "").strip()
    if question:
        ss.history.append({"role": "user", "content": question})

        # compute allowed_ids once
        allowed_ids = ss.scope_ids if ss.scope_mode == "Selected documents" else None

        if chat_mode == "Docs-only":
            context, files, score = fetch_context_with_mmr(question, k=5, widen=6, allowed_ids=allowed_ids)
            if not context:
                msgs = [{"role":"system","content":PROMPT_SYSTEM},
                        {"role":"user","content":"No matching context in selected docs. " + question}]
                final = stream_or_call(msgs)
                ss.history.append({"role":"assistant","content":final})
            else:
                msgs = [{"role":"system","content":PROMPT_SYSTEM},
                        {"role":"user","content":f"Question: {question}\n\nContext:\n{context}"}]
                final = stream_or_call(msgs)
                ss.history.append({"role":"assistant","content":final})
                if files: st.caption("Sources: " + ", ".join(files))

        elif chat_mode == "General LLM":
            msgs = [{"role":"system","content":PROMPT_SYSTEM},
                    {"role":"user","content":question}]
            final = stream_or_call(msgs)
            ss.history.append({"role":"assistant","content":final})

        else:  # Auto (smart)
            context, files, score = fetch_context_with_mmr(question, k=5, widen=6, allowed_ids=allowed_ids)
            if context and score >= 0.28:
                msgs = [{"role":"system","content":PROMPT_SYSTEM},
                        {"role":"user","content":f"Question: {question}\n\nContext:\n{context}"}]
                final = stream_or_call(msgs)
                ss.history.append({"role":"assistant","content":final})
                if files: st.caption("Sources: " + ", ".join(files))
            else:
                msgs = [{"role":"system","content":PROMPT_SYSTEM},
                        {"role":"user","content":question}]
                final = stream_or_call(msgs)
                ss.history.append({"role":"assistant","content":final})

    ss._clear_input = True
    st.rerun()

# history render
for msg in ss.history:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

st.write("")
st.caption("Tip: Choose **Document scope → Selected documents** to restrict answers to specific files.")
