"""
Load documents into ChromaDB using a selectable chunking strategy.

Usage:
    python load_data.py                          # defaults: sentence strategy, ./sample_data
    python load_data.py --strategy recursive     # pick a strategy
    python load_data.py --data-dir /path/to/docs # custom data directory
"""

import argparse
import os
import sys

import chromadb
from pypdf import PdfReader

from chunkers import STRATEGIES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(SCRIPT_DIR, "sample_data")
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "rag_documents"


def read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_documents(data_dir: str) -> list[tuple[str, str]]:
    """Returns list of (filename, full_text) tuples."""
    documents = []
    for filename in sorted(os.listdir(data_dir)):
        filepath = os.path.join(data_dir, filename)
        if filename.lower().endswith(".txt"):
            documents.append((filename, read_txt(filepath)))
        elif filename.lower().endswith(".pdf"):
            documents.append((filename, read_pdf(filepath)))
    return documents


def main():
    parser = argparse.ArgumentParser(description="Load documents with smart chunking")
    parser.add_argument(
        "--strategy",
        choices=list(STRATEGIES.keys()),
        default="sentence",
        help="Chunking strategy to use (default: sentence)",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Directory containing .txt/.pdf files",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        print(f"Error: directory '{args.data_dir}' not found.")
        sys.exit(1)

    chunk_fn = STRATEGIES[args.strategy]
    print(f"Strategy : {args.strategy}")
    print(f"Data dir : {args.data_dir}\n")

    documents = load_documents(args.data_dir)
    if not documents:
        print("No .txt or .pdf files found.")
        sys.exit(1)

    print(f"Found {len(documents)} document(s)")

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    all_ids = []
    all_chunks = []
    all_metadatas = []

    for filename, text in documents:
        chunks = chunk_fn(text)
        print(f"  {filename}: {len(chunks)} chunk(s)")
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{filename}::chunk_{i}")
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": filename,
                "chunk": i,
                "strategy": args.strategy,
            })

    collection.add(ids=all_ids, documents=all_chunks, metadatas=all_metadatas)

    print(f"\nStored {len(all_chunks)} chunks in ChromaDB at: {CHROMA_DB_DIR}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()
