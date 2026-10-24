"""Load policy documents, split them into section-level chunks, and index them in ChromaDB.

Each policy file is organised as:
    # P01: Title
    ## P01-1.2 Section heading
    section text...

One chunk = one section. Policy sections are short and self-contained, so section-level
chunking keeps each answer in a single chunk and gives precise citations (e.g. [P01-1.2]).
"""
import re
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parent.parent
POLICY_DIR = ROOT / "data" / "policies"
DB_DIR = ROOT / "chroma_db"
COLLECTION = "policies"

SECTION_RE = re.compile(r"^## (\S+) (.+)$")
TITLE_RE = re.compile(r"^# (\S+): (.+)$")


def parse_policy(path: Path):
    """Return a list of chunk dicts for one policy file."""
    doc_id, doc_title = path.stem, path.stem
    chunks, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        m_title = TITLE_RE.match(line)
        if m_title:
            doc_id, doc_title = m_title.group(1), m_title.group(2).strip()
            continue
        m_sec = SECTION_RE.match(line)
        if m_sec:
            if current:
                chunks.append(current)
            current = {
                "id": m_sec.group(1),
                "doc_id": doc_id,
                "doc_title": doc_title,
                "heading": m_sec.group(2).strip(),
                "lines": [],
            }
        elif current is not None and line.strip():
            current["lines"].append(line.strip())
    if current:
        chunks.append(current)
    for c in chunks:
        c["text"] = " ".join(c.pop("lines"))
    return chunks


def main():
    files = sorted(POLICY_DIR.glob("*.md"))
    if not files:
        sys.exit(f"No policy files found in {POLICY_DIR}")

    chunks = []
    for f in files:
        chunks.extend(parse_policy(f))

    ids = [c["id"] for c in chunks]
    if len(ids) != len(set(ids)):
        sys.exit("Duplicate section IDs found; every '## ' heading needs a unique ID.")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(COLLECTION)  # rebuild from scratch each run
    except Exception:
        pass
    # Cosine distance suits text embeddings. Chroma's default embedding function runs locally.
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    col.add(
        ids=ids,
        documents=[f"{c['doc_title']} - {c['heading']}. {c['text']}" for c in chunks],
        metadatas=[
            {"doc_id": c["doc_id"], "doc_title": c["doc_title"], "heading": c["heading"], "text": c["text"]}
            for c in chunks
        ],
    )
    print(f"Indexed {len(chunks)} chunks from {len(files)} policy documents into {DB_DIR}")


if __name__ == "__main__":
    main()
