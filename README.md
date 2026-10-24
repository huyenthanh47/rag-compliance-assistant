# RAG Compliance Assistant (CS6303 final project)

A Retrieval-Augmented Generation assistant that answers employee questions about the internal
policies of a **fictional** clinic ("Northside Family Clinic"), citing the policy section it used.
The project also evaluates prompt-injection attacks against the retrieval pipeline and defenses
against them (attack and defense experiments are the next stage; see Status).

All documents are synthetic or public. No real patient or company data is used.

## Status

| Part | Status |
|------|--------|
| Synthetic policy corpus (7 documents, 40 sections) | done |
| Chunking + ChromaDB indexing (`src/ingest.py`) | done |
| Retrieval + grounded answer with citations (`src/ask.py`) | done (baseline, no defenses) |
| Retrieval evaluation, 10 questions (`src/eval_retrieval.py`) | done |
| Poisoned documents and attack measurement | planned |
| Defenses (injection filter, delimited context, ingestion checks) | planned |
| Streamlit interface | planned |

## Requirements

- Python 3.10 or newer
- OS: tested on Linux; should also run on macOS and Windows
- Packages: `anthropic`, `chromadb`, `python-dotenv` (see `requirements.txt`)
- An Anthropic API key (only needed for generating answers, not for the retrieval-only evaluation)
- First run of `ingest.py` downloads a small local embedding model (internet needed once)

## How to run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then edit .env and paste your own API key

python src/ingest.py                                   # build the vector index
python src/ask.py "Can I email patient records to my Gmail?"   # ask one question
python src/eval_retrieval.py                           # retrieval accuracy on 10 questions (no API key)
python src/eval_retrieval.py --answer                  # also generate answers for manual grading
```

Results are written to `eval/results/`. Every answer from `ask.py` is appended to `logs/audit.jsonl`.

## Layout

```
data/policies/        7 synthetic policy documents (one section = one chunk)
eval/questions.json   10 test questions with answer key + 2 out-of-scope questions
src/ingest.py         parse, chunk, embed, index
src/ask.py            retrieve + grounded generation with citations + audit log
src/eval_retrieval.py retrieval hit-rate and optional answer generation
```

## Security notes

- Never commit `.env`; it is excluded by `.gitignore`. Commit only `.env.example`.
- The baseline prompt intentionally has **no** instruction to treat retrieved text as untrusted,
  so later experiments can measure the effect of each defense separately.
