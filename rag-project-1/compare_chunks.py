"""
Compare all three chunking strategies side-by-side on the same document.

Usage:
    python compare_chunks.py                        # uses first file in ./sample_data
    python compare_chunks.py path/to/file.txt       # specific file
"""

import os
import sys

from chunkers import STRATEGIES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(SCRIPT_DIR, "sample_data")


def pick_file(path: str | None) -> str:
    """Return a file path: use the argument, or grab the first .txt from sample_data."""
    if path and os.path.isfile(path):
        return path

    if os.path.isdir(DEFAULT_DATA_DIR):
        for f in sorted(os.listdir(DEFAULT_DATA_DIR)):
            if f.lower().endswith(".txt"):
                return os.path.join(DEFAULT_DATA_DIR, f)

    print("No file found. Pass a file path as an argument.")
    sys.exit(1)


def preview(text: str, max_len: int = 80) -> str:
    """Truncate text for display."""
    one_line = text.replace("\n", " ").strip()
    if len(one_line) > max_len:
        return one_line[: max_len - 3] + "..."
    return one_line


def main():
    filepath = pick_file(sys.argv[1] if len(sys.argv) > 1 else None)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"File: {filepath}")
    print(f"Total length: {len(text)} characters\n")
    print("=" * 90)

    for name, chunk_fn in STRATEGIES.items():
        chunks = chunk_fn(text)
        total_chars = sum(len(c) for c in chunks)

        print(f"\n  Strategy: {name}")
        print(f"  Chunks: {len(chunks)}  |  Avg size: {total_chars // max(len(chunks), 1)} chars")
        print(f"  {'─' * 80}")

        for i, chunk in enumerate(chunks):
            print(f"    [{i:>3}] ({len(chunk):>4} chars) {preview(chunk)}")

        print(f"\n{'=' * 90}")


if __name__ == "__main__":
    main()
