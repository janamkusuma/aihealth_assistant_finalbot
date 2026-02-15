# app/rag/ingest.py

import os

from app.config import settings
from app.rag.vectorstore import upsert_document_to_namespace

# Allowed file types
ALLOWED = {".pdf", ".txt", ".md"}


def ingest_folder_to_pinecone():
    """
    Reads DATA_DIR folder → chunks → embeddings → Pinecone namespace.
    Safe version (no crash, clear logs).
    """
    print("\n🚀 Starting Pinecone ingest...")

    folder = getattr(settings, "DATA_DIR", "")
    namespace = getattr(settings, "PINECONE_NAMESPACE", "global-medical")

    # -------- Checks --------
    if not folder:
        print("⚠️ DATA_DIR not set in .env")
        return

    if not os.path.exists(folder):
        print(f"⚠️ Folder not found: {folder}")
        return

    if getattr(settings, "VECTOR_BACKEND", "").lower() != "pinecone":
        print("ℹ️ VECTOR_BACKEND not pinecone → skipping ingest")
        return

    if not getattr(settings, "PINECONE_API_KEY", ""):
        print("⚠️ Pinecone API key missing")
        return

    print(f"📂 DATA_DIR = {folder}")
    print(f"📌 Namespace = {namespace}")

    count = 0
    skipped = 0

    # -------- Index files --------
    for root, _, files in os.walk(folder):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in ALLOWED:
                skipped += 1
                continue

            path = os.path.join(root, fn)
            try:
                print(f"➡️ Processing: {fn}")
                upsert_document_to_namespace(namespace=namespace, filepath=path)
                count += 1
                print(f"✅ Indexed: {fn}")
            except Exception as e:
                print(f"❌ Failed: {fn}")
                print(" Error:", e)

    # -------- Final log --------
    print("\n🎉 Ingest complete")
    print(f" Indexed files : {count}")
    print(f" Skipped files : {skipped}")
    print(f" Namespace : {namespace}")
