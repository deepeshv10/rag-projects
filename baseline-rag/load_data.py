import os
import sys
import chromadb
from pypdf import PdfReader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(SCRIPT_DIR, "sample_data")
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "rag_documents"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def read_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


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
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA_DIR

    if not os.path.isdir(data_dir):
        print(f"Error: directory '{data_dir}' not found.")
        sys.exit(1)

    print(f"Loading documents from: {data_dir}")
    documents = load_documents(data_dir)

    if not documents:
        print("No .txt or .pdf files found in the directory.")
        sys.exit(1)

    print(f"Found {len(documents)} document(s)")

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    # Recreate collection to avoid duplicates on re-run
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    all_ids = []
    all_chunks = []
    all_metadatas = []

    for filename, text in documents:
        chunks = chunk_text(text)
        print(f"  {filename}: {len(chunks)} chunk(s)")
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{filename}::chunk_{i}")
            all_chunks.append(chunk)
            all_metadatas.append({"source": filename, "chunk": i})

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        metadatas=all_metadatas,
    )

    print(f"\nStored {len(all_chunks)} chunks in ChromaDB at: {CHROMA_DB_DIR}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()
