"""
Query the ChromaDB collection and get answers from Gemini.
Identical to the baseline RAG lookup, just points to this project's DB.
"""

import os

import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.join(SCRIPT_DIR, "chroma_db")
COLLECTION_NAME = "rag_documents"

TOP_K = 3

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant. Answer the user's question based ONLY on the "
    "provided context below. If the context does not contain enough information "
    "to answer the question, say so clearly. Do not make up information."
)


def get_gemini_client() -> genai.Client:
    load_dotenv(os.path.join(SCRIPT_DIR, "..", ".env"))
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Check your .env file.")
    return genai.Client(api_key=api_key)


def query_chromadb(query: str, n_results: int = TOP_K):
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)
    return collection.query(query_texts=[query], n_results=n_results)


def build_prompt(query: str, context_chunks: list[str], sources: list[dict]) -> str:
    context_parts = []
    for i, (chunk, meta) in enumerate(zip(context_chunks, sources), 1):
        context_parts.append(f"[Source {i}: {meta['source']}, chunk {meta['chunk']}]\n{chunk}")

    context_block = "\n\n---\n\n".join(context_parts)
    return f"Context:\n{context_block}\n\nQuestion: {query}"


def main():
    if not os.path.isdir(CHROMA_DB_DIR):
        print("Error: ChromaDB not found. Run load_data.py first.")
        return

    gemini_client = get_gemini_client()
    print("RAG Lookup Ready — Project 1: Smart Chunking (type 'quit' to exit)\n")

    while True:
        query = input("Your question: ").strip()
        if not query or query.lower() == "quit":
            print("Goodbye!")
            break

        results = query_chromadb(query)
        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        print(f"\n--- Retrieved {len(chunks)} chunk(s) ---")
        for i, (meta, dist) in enumerate(zip(metadatas, distances), 1):
            strategy = meta.get("strategy", "unknown")
            print(f"  [{i}] {meta['source']} (chunk {meta['chunk']}, {strategy}) | distance: {dist:.4f}")

        prompt = build_prompt(query, chunks, metadatas)

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            ),
        )

        print(f"\n--- Answer ---\n{response.text}\n")


if __name__ == "__main__":
    main()
