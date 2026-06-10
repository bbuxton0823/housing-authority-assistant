#!/usr/bin/env python3
"""
Build the Housing Authority knowledge base (RAG) from the documents in rag_docs/.

Creates (or updates) an OpenAI hosted vector store, uploads every PDF in
rag_docs/, waits for processing, and writes VECTOR_STORE_ID into .env so the
agents pick it up via the FileSearchTool.

Contents are PUBLIC documents only (HUD guidance, NSPIRE standards, the HACSM
Administrative Plan, and California housing law guides). Never upload anything
containing tenant PII to this store.

Usage:
    python build_rag.py            # create/refresh the knowledge base
    python build_rag.py --status   # show current store contents
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import openai

STORE_NAME = "housing-authority-kb"
DOCS_DIR = Path(__file__).parent / "rag_docs"
ENV_PATH = Path(__file__).parent / ".env"


def get_client() -> openai.OpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Add it to python-backend/.env first.")
    return openai.OpenAI(api_key=key)


def find_or_create_store(client: openai.OpenAI):
    existing_id = os.getenv("VECTOR_STORE_ID", "").strip()
    if existing_id:
        try:
            return client.vector_stores.retrieve(existing_id)
        except Exception:
            print(f"Existing VECTOR_STORE_ID {existing_id} not found; creating a new store.")
    return client.vector_stores.create(name=STORE_NAME)


def write_env_var(key: str, value: str):
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    out, found = [], False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"\n# RAG knowledge base (created by build_rag.py)\n{key}={value}")
    ENV_PATH.write_text("\n".join(out) + "\n")


def main():
    client = get_client()

    if "--status" in sys.argv:
        sid = os.getenv("VECTOR_STORE_ID", "").strip()
        if not sid:
            sys.exit("No VECTOR_STORE_ID in .env yet. Run: python build_rag.py")
        store = client.vector_stores.retrieve(sid)
        print(f"Store: {store.name} ({store.id}) - {store.file_counts.completed} files ready")
        for f in client.vector_stores.files.list(vector_store_id=sid):
            fileinfo = client.files.retrieve(f.id)
            print(f"  [{f.status}] {fileinfo.filename}")
        return

    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {DOCS_DIR}. Add source documents first.")

    store = find_or_create_store(client)
    print(f"Vector store: {store.name} ({store.id})")
    # Persist the ID immediately so interrupted runs resume into the same store
    write_env_var("VECTOR_STORE_ID", store.id)
    os.environ["VECTOR_STORE_ID"] = store.id

    # Skip files already uploaded (by filename)
    existing = set()
    try:
        for f in client.vector_stores.files.list(vector_store_id=store.id):
            existing.add(client.files.retrieve(f.id).filename)
    except Exception:
        pass

    for pdf in pdfs:
        if pdf.name in existing:
            print(f"  skip (already uploaded): {pdf.name}")
            continue
        print(f"  uploading: {pdf.name} ({pdf.stat().st_size // 1024} KB)")
        with open(pdf, "rb") as fh:
            client.vector_stores.files.upload_and_poll(vector_store_id=store.id, file=fh)

    # Wait for processing to finish
    for _ in range(60):
        store = client.vector_stores.retrieve(store.id)
        fc = store.file_counts
        if fc.in_progress == 0:
            break
        print(f"  processing... {fc.completed}/{fc.total}")
        time.sleep(5)

    print(f"Done: {store.file_counts.completed}/{store.file_counts.total} files ready, "
          f"{store.file_counts.failed} failed.")
    write_env_var("VECTOR_STORE_ID", store.id)
    print(f"VECTOR_STORE_ID={store.id} written to .env")
    print("Restart the backend to enable knowledge-base search.")


if __name__ == "__main__":
    main()
