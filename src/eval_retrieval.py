"""Measure retrieval accuracy on eval/questions.json, and optionally generate answers.

Usage:
    python src/eval_retrieval.py              # retrieval only (no API key needed)
    python src/eval_retrieval.py --answer     # also ask Claude and save answers for manual grading
    python src/eval_retrieval.py --k 5        # change how many sections are retrieved

Retrieval hit = at least one expected section appears in the top-k results.
Answer correctness must be judged MANUALLY against 'expected_answer'; the keyword check
printed with --answer is only a quick hint.
"""
import argparse
import json
from pathlib import Path

from ask import NOT_COVERED, answer, retrieve

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "eval" / "questions.json"
OUT_DIR = ROOT / "eval" / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--answer", action="store_true", help="also generate answers with Claude")
    args = ap.parse_args()

    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    rows, hits = [], 0

    print(f"Retrieval evaluation (top-{args.k})\n" + "-" * 60)
    for q in data["questions"]:
        chunks = retrieve(q["question"], args.k)
        got = [c["id"] for c in chunks]
        hit = any(s in got for s in q["expected_sections"])
        hits += hit
        row = {"id": q["id"], "question": q["question"], "expected": q["expected_sections"], "retrieved": got, "hit": hit}
        if args.answer:
            res = answer(q["question"], args.k, log=False)
            row["answer"] = res["answer"]
            row["expected_answer"] = q["expected_answer"]
            row["keyword_hint"] = all(k.lower() in res["answer"].lower() for k in q["answer_keywords"])
        rows.append(row)
        print(f"{q['id']:>4}  {'HIT ' if hit else 'MISS'}  expected {q['expected_sections']}  got {got}")

    total = len(data["questions"])
    print("-" * 60)
    print(f"Retrieved a correct supporting section: {hits}/{total}")

    out = {"k": args.k, "retrieval_hits": hits, "total": total, "rows": rows}

    if args.answer:
        print("\nOut-of-scope questions (should answer: '" + NOT_COVERED + "')")
        oos_rows, refused = [], 0
        for q in data["out_of_scope"]:
            res = answer(q["question"], args.k, log=False)
            ok = NOT_COVERED.lower() in res["answer"].lower()
            refused += ok
            oos_rows.append({"id": q["id"], "question": q["question"], "answer": res["answer"], "correct_refusal": ok})
            print(f"{q['id']:>4}  {'REFUSED' if ok else 'ANSWERED'}  {res['answer'][:90]}")
        print(f"Correct refusals: {refused}/{len(data['out_of_scope'])}")
        out["out_of_scope"] = oos_rows
        print("\nNow read eval/results/*.json and mark each answer correct or incorrect yourself.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / ("retrieval_and_answers.json" if args.answer else "retrieval_only.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
