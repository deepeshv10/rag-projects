# Project 1 — Smarter Chunking

## What This Project Does

The baseline RAG pipeline splits text into fixed 500-character windows. This often cuts
mid-word and mid-sentence, producing chunks that lack semantic coherence.

This project replaces that with three chunking strategies you can compare:

| Strategy    | How it works                                                         |
| ----------- | -------------------------------------------------------------------- |
| `fixed`     | Baseline — 500-char windows with 50-char overlap (same as `src/rag`) |
| `sentence`  | Groups whole sentences until the chunk approaches 500 chars           |
| `recursive` | Splits by paragraph first, then by sentence, then by character       |

## Files

```
rag-project-1/
├── README.md
├── requirements.txt
├── chunkers.py           # the three chunking strategies
├── load_data.py          # ingest documents into ChromaDB (--strategy flag)
├── lookup_data.py        # query ChromaDB + Gemini (same as baseline)
├── compare_chunks.py     # see how each strategy chunks the same file
└── sample_data/
    └── cloud_computing.txt
```

## Setup

```bash
cd src/rag-project-1
pip install -r requirements.txt
```

## Usage

### 1. Compare chunking strategies (no DB needed)

```bash
python compare_chunks.py
```

This prints a side-by-side view of how each strategy chunks `cloud_computing.txt`.
You can also pass a specific file:

```bash
python compare_chunks.py path/to/any_file.txt
```

### 2. Load documents into ChromaDB

```bash
# default strategy: sentence
python load_data.py

# pick a strategy
python load_data.py --strategy fixed
python load_data.py --strategy sentence
python load_data.py --strategy recursive

# use a custom data directory
python load_data.py --strategy recursive --data-dir /path/to/docs
```

### 3. Ask questions

```bash
python lookup_data.py
```

This starts a CLI loop where you can ask questions. The retrieved chunks show which
strategy was used to create them.

## Learning Workflow

1. Run `compare_chunks.py` first to see how the three strategies differ on the same text.
2. Load with `--strategy fixed`, ask a question, note the answer quality.
3. Re-load with `--strategy sentence`, ask the same question, compare.
4. Re-load with `--strategy recursive`, ask again, compare.

This lets you see first-hand how chunking quality affects retrieval and final answers.
