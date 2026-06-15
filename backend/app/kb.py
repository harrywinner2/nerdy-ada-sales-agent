"""Knowledge base — grounded retrieval so Ada never invents policy, pricing, or competitive
facts. Docs are embedded with text-embedding-3-small and retrieved by cosine similarity.

`lookup` returns the top-k chunks AND a compact citation string the model is told to ground
its answer in. If nothing clears the relevance floor, we return an explicit "no grounded
answer" signal so Ada says she'll check / escalates instead of hallucinating."""
from __future__ import annotations

import struct

import numpy as np

from . import db
from .openai_client import embed

_FLOOR = 0.28  # cosine floor below which we treat the KB as having no answer


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack(blob: bytes) -> np.ndarray:
    n = len(blob) // 4
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


async def index_doc(doc_id: str, title: str, category: str, content: str) -> None:
    vec = (await embed([f"{title}\n{content}"]))[0]
    db.execute(
        """INSERT INTO kb_docs (id, title, category, content, embedding)
           VALUES (?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET title=excluded.title, category=excluded.category,
             content=excluded.content, embedding=excluded.embedding""",
        (doc_id, title, category, content, _pack(vec)),
    )


def list_docs() -> list[dict]:
    return db.query("SELECT id, title, category, content FROM kb_docs ORDER BY category, title")


def doc_count() -> int:
    row = db.query_one("SELECT COUNT(*) AS n FROM kb_docs")
    return int(row["n"]) if row else 0


async def lookup(querytext: str, k: int = 3) -> dict:
    """Returns {grounded: bool, answer_context: str, citations: [...], scores: [...]}"""
    rows = db.query("SELECT id, title, category, content, embedding FROM kb_docs")
    if not rows:
        return {"grounded": False, "answer_context": "", "citations": [], "scores": []}
    qvec = np.array((await embed([querytext_norm(querytext)]))[0], dtype=np.float32)
    qn = qvec / (np.linalg.norm(qvec) + 1e-9)
    scored = []
    for r in rows:
        if not r["embedding"]:
            continue
        v = _unpack(r["embedding"])
        v = v / (np.linalg.norm(v) + 1e-9)
        scored.append((float(np.dot(qn, v)), r))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]
    grounded = bool(top and top[0][0] >= _FLOOR)
    citations = [{"id": r["id"], "title": r["title"], "category": r["category"],
                 "score": round(s, 3)} for s, r in top if s >= _FLOOR]
    context = "\n\n".join(f"[{r['title']}] {r['content']}" for s, r in top if s >= _FLOOR)
    return {
        "grounded": grounded,
        "answer_context": context,
        "citations": citations,
        "scores": [round(s, 3) for s, _ in top],
    }


def querytext_norm(t: str) -> str:
    return " ".join(t.strip().split())[:512]
