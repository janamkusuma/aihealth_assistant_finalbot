# app/rag/vectorstore.py

import os
import uuid
from typing import List, Optional

from pinecone import Pinecone

from app.config import settings

# ---------------------------
# Pinecone clients
# ---------------------------
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX)

# IMPORTANT:
# Your Pinecone index is 384-dim (as you printed).
# So embed model MUST also output 384 dims.
# Your index embed model is: llama-text-embed-v2 (384)
EMBED_MODEL = getattr(settings, "PINECONE_EMBED_MODEL", "llama-text-embed-v2")


def _embed_texts(texts: List[str], *, input_type: str) -> List[List[float]]:
    """
    Pinecone Inference embeddings (NO local model)
    input_type: "passage" for docs, "query" for question
    """
    res = pc.inference.embed(
        model=EMBED_MODEL,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return [x["values"] for x in res.data]


def _embed_query(q: str) -> List[float]:
    return _embed_texts([q], input_type="query")[0]


def _chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + max_chars])
        i += max_chars - overlap
    return chunks


def _read_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()

    if ext in [".txt", ".md"]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    if ext == ".pdf":
        from app.rag.pdf_utils import extract_text_from_pdf
        return extract_text_from_pdf(filepath)

    return ""


def _upsert_chunks(
    namespace: str,
    source_name: str,
    chat_id: Optional[int],
    chunks: List[str],
):
    if not chunks:
        return

    BATCH = 12  # keep requests small
    for i in range(0, len(chunks), BATCH):
        part = chunks[i : i + BATCH]
        vectors = _embed_texts(part, input_type="passage")

        to_upsert = []
        for chunk, vec in zip(part, vectors):
            vid = str(uuid.uuid4())
            md = {
                "source": source_name,
                "text": chunk,
            }
            if chat_id is not None:
                md["chat_id"] = chat_id

            to_upsert.append({"id": vid, "values": vec, "metadata": md})

        # ✅ Classic upsert supports metadata dict
        index.upsert(vectors=to_upsert, namespace=namespace)


# ---------------------------
# CHAT UPLOAD -> chat-{chat_id}
# ---------------------------
def upsert_document_to_chat(chat_id: int, filepath: str):
    namespace = f"chat-{chat_id}"
    text = _read_file(filepath)
    if not text.strip():
        return

    chunks = _chunk_text(text)
    _upsert_chunks(
        namespace=namespace,
        source_name=os.path.basename(filepath),
        chat_id=chat_id,
        chunks=chunks,
    )


# ---------------------------
# GLOBAL DATASET -> namespace (global-medical)
# ---------------------------
def upsert_document_to_namespace(namespace: str, filepath: str):
    text = _read_file(filepath)
    if not text.strip():
        return

    chunks = _chunk_text(text)
    _upsert_chunks(
        namespace=namespace,
        source_name=os.path.basename(filepath),
        chat_id=None,
        chunks=chunks,
    )


def retrieve_context_for_chat(chat_id: int, query: str, top_k: int = 4) -> str:
    namespace = f"chat-{chat_id}"
    qvec = _embed_query(query)

    res = index.query(
        namespace=namespace,
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
    )

    matches = (res.get("matches") or [])
    texts: List[str] = []
    for m in matches:
        md = (m.get("metadata") or {})
        t = md.get("text")
        if t:
            texts.append(t)

    return "\n\n".join(texts).strip()


def retrieve_context_from_namespace(namespace: str, query: str, top_k: int = 4) -> str:
    qvec = _embed_query(query)

    res = index.query(
        namespace=namespace,
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
    )

    matches = (res.get("matches") or [])
    texts: List[str] = []
    for m in matches:
        md = (m.get("metadata") or {})
        t = md.get("text")
        if t:
            texts.append(t)

    return "\n\n".join(texts).strip()
