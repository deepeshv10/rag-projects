# rag-projects
Repository for RAG projects

In this repo, I will be creating multiple phase-wise enhancements (as Projects) to make a Production ready RAG system.

Starting with very basic-rag : It uses local embedding model (all-MiniLM-L6-v2) for loading data in ChromaDB, and Gemini 2.5 flash lite for Lookup/inferencing.

# RAG Enhancement Roadmap

A collection of capabilities to incrementally improve the basic RAG pipeline (ChromaDB + Gemini). Each section is scoped as a standalone project.

---

## Current Baseline

| Layer              | Implementation                                  |
| ------------------ | ----------------------------------------------- |
| Document ingestion | `.txt` and `.pdf` only                          |
| Chunking           | Fixed 500-char window, 50-char overlap          |
| Embeddings         | ChromaDB default (all-MiniLM-L6-v2)             |
| Retrieval          | Single-vector similarity search, top-3          |
| Generation         | Single Gemini call with a grounding system prompt |
| Interface          | CLI input loop                                  |

---

## Project 1 — Smarter Chunking

**Goal:** Produce semantically coherent chunks instead of splitting mid-word/mid-sentence.

### Approaches

- **Sentence-aware chunking** — split on sentence boundaries so each chunk is a complete thought.
- **Recursive / hierarchical chunking** — split by paragraph first, then by sentence if a paragraph exceeds the size limit. LangChain's `RecursiveCharacterTextSplitter` implements this.
- **Semantic chunking** — compute embedding similarity between consecutive sentences; place split boundaries where similarity drops.

### Key Decisions

- Target chunk size (tokens vs. characters).
- How much overlap to keep for continuity.
- Whether to preserve document structure (headings, lists) as metadata.

---

## Project 2 — Better Embeddings

**Goal:** Replace the default small embedding model with a higher-quality one.

### Approaches

- Use **Gemini's embedding model** (`models/text-embedding-004`, 768-dim) — already accessible via the existing API key.
- Pass a custom `embedding_function` to ChromaDB's `create_collection` / `get_collection` so both ingestion and query use the same model.

### Key Decisions

- Batch size for embedding API calls during ingestion.
- Whether to store raw text alongside vectors for debugging.
- Cost implications for large document sets (Gemini embedding API pricing).

---

## Project 3 — Hybrid Search (Keyword + Semantic)

**Goal:** Catch exact-match queries (product codes, acronyms, names) that pure vector search misses.

### Approaches

- Add **BM25 keyword scoring** (e.g. via `rank_bm25`) alongside vector similarity.
- Combine ranked lists using **Reciprocal Rank Fusion (RRF)**.
- Use ChromaDB's **metadata filtering** (`where` clauses) to scope retrieval by source file, date, document type, etc.

### Key Decisions

- Weighting between keyword and semantic scores.
- Whether to pre-filter by metadata before scoring or post-filter.
- Index maintenance strategy when documents are updated.

---

## Project 4 — Query Transformation

**Goal:** Improve retrieval quality by reformulating the user's raw question before searching.

### Approaches

- **HyDE (Hypothetical Document Embeddings)** — ask the LLM to generate a hypothetical answer, then embed *that* to search. Often retrieves more relevant chunks.
- **Query expansion / rewriting** — have the LLM rephrase the question into 2–3 alternative search queries, retrieve for each, then deduplicate.
- **Step-back prompting** — ask a broader contextual question first to gather background, then answer the specific question.

### Key Decisions

- Extra latency from the additional LLM call(s).
- How many expanded queries to run (cost vs. recall trade-off).
- Whether to show the rewritten query to the user for transparency.

---

## Project 5 — Re-ranking

**Goal:** Re-score retrieved chunks so the most relevant ones appear first in the prompt.

### Approaches

- Use a **cross-encoder reranker** (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`) to re-order the top-K results.
- Use **Gemini as a reranker** — ask it to score each chunk's relevance to the question on a 1–5 scale, then keep only high-scoring chunks.
- **Cohere Rerank API** — a hosted reranker if you prefer not to run a model locally.

### Key Decisions

- How many candidates to retrieve before reranking (top-10 → rerank → top-3).
- Latency budget for the reranking step.
- Local model vs. API-based reranker.

---

## Project 6 — Conversation Memory

**Goal:** Support multi-turn conversations so follow-up questions work naturally.

### Approaches

- Maintain a **chat history buffer** — pass the last N turns as additional context to the LLM.
- **Context-aware query rewriting** — use the LLM to rewrite the user's latest message into a standalone question given the conversation history (e.g. "What about the second one?" → "What is the price of Product B?").
- Store history in memory for the CLI; persist to a file or database for a web app.

### Key Decisions

- Maximum history window (token budget).
- Whether to summarize older turns to save context space.
- How rewritten queries interact with retrieval (search with original vs. rewritten).

---

## Project 7 — Citation & Source Attribution

**Goal:** Let the user verify answers by tracing them back to specific source chunks.

### Approaches

- Instruct the model to **cite source numbers** inline (e.g. `[Source 1]`, `[Source 2]`).
- Return the **retrieved text snippets** alongside the answer so the user can cross-reference.
- Highlight or link to the original document and chunk index.

### Key Decisions

- Citation format (inline tags, footnotes, side panel).
- Whether to show confidence/distance scores to the user.
- How to handle answers that synthesize across multiple sources.

---

## Project 8 — More File Formats

**Goal:** Expand the set of documents the pipeline can ingest.

### Formats to Add

| Format       | Library              |
| ------------ | -------------------- |
| Markdown     | Built-in string read |
| Word (`.docx`) | `python-docx`        |
| HTML         | `beautifulsoup4`     |
| CSV          | `csv` / `pandas`     |
| PowerPoint   | `python-pptx`        |
| JSON         | Built-in `json`      |

### Key Decisions

- How to handle structured data (CSV rows → natural-language statements before chunking).
- Whether to strip formatting or preserve it as metadata.
- File-type detection (extension-based vs. magic bytes).

---

## Project 9 — Streaming Responses

**Goal:** Display tokens as they are generated instead of waiting for the full response.

### Approaches

- Use Gemini's `generate_content_stream` method — returns an iterator of partial responses.
- Print each chunk to stdout immediately for the CLI.
- For a web UI, use Server-Sent Events (SSE) or WebSockets.

### Key Decisions

- How to handle errors mid-stream.
- Whether to buffer for sentence-level display vs. token-level.
- Interaction with citation formatting (citations may appear at the end).

---

## Project 10 — Evaluation & Guardrails

**Goal:** Measure quality and prevent bad answers.

### Guardrails

- **Relevance gating** — if all retrieved chunks have a distance above a threshold, respond with "I don't have information about that" instead of hallucinating.
- **Answer grounding check** — a second LLM call that verifies the generated answer is actually supported by the retrieved context.
- **Input validation** — detect and reject prompt injection attempts.

### Evaluation

- Build a small **test set** of (question, expected answer, relevant source) tuples.
- Measure **retrieval recall** (are the right chunks in the top-K?) and **answer quality** (faithfulness, relevance, completeness).
- Automate with frameworks like `ragas` or `deepeval`.

### Key Decisions

- Distance threshold for relevance gating (requires calibration on your data).
- Cost of the grounding-check LLM call on every query.
- How often to re-run evaluations as the knowledge base changes.

---

## Project 11 — Agentic RAG

**Goal:** Let the LLM decide when and how to retrieve, enabling multi-step reasoning.

### Approaches

- **Function calling** — register `query_chromadb` as a tool the Gemini model can invoke. The model decides *when* to search and *what query* to use.
- **Multi-step retrieval** — the model breaks a complex question into sub-questions, retrieves for each, then synthesizes a final answer.
- **Self-reflection** — after generating an answer, the model evaluates whether it needs more information and triggers another retrieval round.

### Key Decisions

- Maximum number of retrieval rounds (to bound cost and latency).
- Which tools to expose beyond search (e.g. calculator, date lookups, web search).
- Orchestration framework (raw function calling vs. LangChain agents vs. LlamaIndex agents).

---

## Project 12 — Web UI

**Goal:** Replace the CLI with an interactive web interface.

### Approaches

- **Streamlit / Gradio** — rapid prototyping with built-in chat components, file upload, and source display.
- **FastAPI + React** — production-grade setup with a REST/WebSocket API backend and a modern frontend.
- **Chainlit** — purpose-built for LLM chat apps with built-in source citation and streaming support.

### Key Decisions

- Authentication and multi-user support.
- File upload for ad-hoc document ingestion.
- How to display sources (expandable panels, side-by-side, inline links).

---

## Suggested Priority Order

| Priority | Project                  | Effort | Impact |
| -------- | ------------------------ | ------ | ------ |
| 1        | Conversation Memory      | Low    | High   |
| 2        | Relevance Gating         | Low    | High   |
| 3        | Gemini Embeddings        | Low    | Medium |
| 4        | Streaming Responses      | Low    | Medium |
| 5        | Smarter Chunking         | Medium | High   |
| 6        | Citation & Attribution   | Medium | Medium |
| 7        | More File Formats        | Medium | Medium |
| 8        | Query Transformation     | Medium | High   |
| 9        | Re-ranking               | Medium | Medium |
| 10       | Hybrid Search            | Medium | Medium |
| 11       | Web UI                   | High   | High   |
| 12       | Agentic RAG             | High   | High   |
| 13       | Evaluation & Guardrails  | High   | High   |

