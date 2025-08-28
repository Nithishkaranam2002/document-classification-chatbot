# backend/rag/rerank.py
from typing import List, Tuple
import numpy as np

def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na = a / (np.linalg.norm(a) + 1e-9)
    nb = b / (np.linalg.norm(b) + 1e-9)
    return float(np.dot(na, nb))

def mmr_rerank(query_vec: List[float], cand_texts: List[str], cand_vecs: List[List[float]],
               k: int = 5, lambda_mult: float = 0.5) -> List[int]:
    """
    Maximal Marginal Relevance. Returns the indices of selected items.
    """
    q = np.array(query_vec, dtype="float32")
    V = np.array(cand_vecs, dtype="float32")
    sims_q = V @ (q / (np.linalg.norm(q) + 1e-9))
    selected, remaining = [], list(range(len(cand_texts)))
    while remaining and len(selected) < k:
        mmr_scores = []
        for idx in remaining:
            diversity = 0.0
            if selected:
                diversity = max(_cos(V[idx], V[j]) for j in selected)
            score = lambda_mult * sims_q[idx] - (1 - lambda_mult) * diversity
            mmr_scores.append((score, idx))
        mmr_scores.sort(reverse=True)
        best = mmr_scores[0][1]
        selected.append(best)
        remaining.remove(best)
    return selected

# Optional: tiny LLM reranker using Gemini (scores 0..1)
def llm_rerank(question: str, cand_texts: List[str], chat_fn) -> List[int]:
    """
    chat_fn: function that accepts messages -> str (Gemini).
    Returns indices sorted by LLM relevance (desc).
    """
    # very small prompt to score each snippet
    scored = []
    for i, t in enumerate(cand_texts):
        prompt = f"""Rate how relevant the snippet is to the question on 0-1.
Question: {question}
Snippet:
{t[:1500]}
Reply with ONLY a number between 0 and 1."""
        msg = [{"role":"user","content":prompt}]
        try:
            s = chat_fn(msg).strip()
            score = float(s.split()[0])
        except:
            score = 0.0
        scored.append((score, i))
    scored.sort(reverse=True)
    return [i for _, i in scored]
