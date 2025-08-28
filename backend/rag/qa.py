# backend/rag/qa.py

from typing import List, Tuple
from backend.services.gemini import chat_llm, embed_texts
from backend.settings import RAG_K
from backend.rag.rerank import mmr_rerank

PROMPT_SYSTEM = """You are a helpful AI assistant (like ChatGPT).
You can answer general questions and, when document context is provided, you must ground answers in that context.

Rules:
- If you used document context, cite filenames inline like [filename].
- If the requested info isn’t in the provided context, say so briefly, then answer generally if appropriate.
- Be concise, correct, and avoid hallucinations.
"""

def _format_context(hits: List[Tuple[float, dict]], k: int) -> Tuple[str, List[str]]:
    """
    hits: list of (similarity_score, metadata) where metadata has keys:
          'text', 'source_path'
    Returns a context string and unique list of filenames for UI display.
    """
    chunks: List[str] = []
    files: List[str] = []
    for score, meta in hits[:k]:
        fname = meta.get("source_path", "").split("/")[-1]
        files.append(fname)
        chunks.append(f"[{fname}] {meta.get('text', '')}")
    unique_files = list(dict.fromkeys(files))
    return "\n\n---\n\n".join(chunks), unique_files

def _avg_top_sim(hits: List[Tuple[float, dict]], k: int) -> float:
    if not hits:
        return 0.0
    sims = [float(s) for s, _ in hits[:k]]
    return sum(sims) / max(1, len(sims))

def _search_with_rerank(question: str, vecstore, embed_fn, k: int, widen: int = 6):
    """
    1) Retrieve a wider set from the vector store.
    2) Compute embeddings of candidates.
    3) MMR rerank to pick top-k diverse & relevant chunks.
    Returns: hits (re-ranked list of (score, meta)), avg_score
    """
    q_emb = embed_fn(question)  # query embedding
    wide_k = max(k * widen, 30)
    pre_hits = vecstore.search(q_emb, k=wide_k) if vecstore else []
    if not pre_hits:
        return [], 0.0

    cand_texts = [m["text"] for _, m in pre_hits]
    cand_vecs = embed_fn(cand_texts)  # list of vectors
    order = mmr_rerank(q_emb, cand_texts, cand_vecs, k=k, lambda_mult=0.6)
    hits = [pre_hits[i] for i in order]
    return hits, _avg_top_sim(hits, k)

def answer_with_context(question: str, vecstore, embed_fn=embed_texts, k: int = RAG_K):
    """
    Always produce a context-grounded answer (Docs-only mode).
    Uses widened recall + MMR rerank before prompting the LLM.
    """
    hits, score = _search_with_rerank(question, vecstore, embed_fn, k=k)
    context, files = _format_context(hits, k)
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
    ]
    ans = chat_llm(messages)
    return ans, files, score

def route_and_answer(
    question: str,
    vecstore,
    embed_fn=embed_texts,
    k: int = RAG_K,
    min_sim: float = 0.28,
    widen: int = 6,
):
    """
    AUTO router:
      - Retrieve wide, MMR-rerank to k.
      - If avg top-k similarity >= min_sim -> use RAG (grounded).
      - Else -> general LLM (no context).

    Returns: (answer, files_used, used_docs: bool, score: float)
    """
    # No index -> general LLM
    if vecstore is None or getattr(vecstore, "index", None) is None or vecstore.index.ntotal == 0:
        msgs = [{"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": question}]
        return chat_llm(msgs), [], False, 0.0

    hits, score = _search_with_rerank(question, vecstore, embed_fn, k=k, widen=widen)

    if hits and score >= min_sim:
        context, files = _format_context(hits, k)
        msgs = [
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
        ]
        ans = chat_llm(msgs)
        return ans, files, True, score

    # Low confidence → general LLM answer
    msgs = [{"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": question}]
    return chat_llm(msgs), [], False, score
