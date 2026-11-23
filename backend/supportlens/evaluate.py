import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from .classifier import evaluate_classifier
from .knowledge import demo_corpus, read_fixture
from .retrieval import Retriever


def run_evaluation(semantic=False, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    corpus = demo_corpus()
    questions = read_fixture("evaluation.json")
    retriever = Retriever(semantic, model_name)
    runs = []
    for method in ["bm25", "hybrid"]:
        rows = []
        # Warm index creation is excluded from per-question latency, but not hidden in metadata.
        retriever.search("return policy", corpus, method)
        for q in questions:
            started = perf_counter()
            hits = retriever.search(q["question"], corpus, method)
            elapsed = (perf_counter() - started) * 1000
            ranked = list(dict.fromkeys(h["filename"] for h in hits))
            target = q["expected_source"]
            rank = ranked.index(target) + 1 if target in ranked else None
            rows.append(
                {
                    **q,
                    "retrieved": ranked,
                    "rank": rank,
                    "abstained": not bool(hits),
                    "passed": rank is not None if target else not bool(hits),
                    "latency_ms": round(elapsed, 2),
                }
            )
        answerable = [r for r in rows if r["expected_source"]]
        unknown = [r for r in rows if not r["expected_source"]]
        runs.append(
            {
                "method": method,
                "recall_at_3": round(
                    sum(r["rank"] is not None for r in answerable) / len(answerable), 4
                ),
                "mrr_at_3": round(
                    sum(1 / r["rank"] if r["rank"] else 0 for r in answerable)
                    / len(answerable),
                    4,
                ),
                "unknown_abstention_rate": round(
                    sum(r["abstained"] for r in unknown) / len(unknown), 4
                ),
                "mean_latency_ms": round(
                    sum(r["latency_ms"] for r in rows) / len(rows), 2
                ),
                "cases": rows,
            }
        )
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "SupportLens synthetic demo benchmark v1",
        "question_count": len(questions),
        "answerable_count": len(answerable),
        "unknown_count": len(unknown),
        "retrieval_mode": "BM25 + sentence embeddings" if semantic else "BM25 + TF-IDF",
        "limitations": "Small, hand-authored synthetic benchmark, not independent real-world validation. Retrieval metrics do not measure generated-answer correctness. Thresholds are heuristic. Latencies use a warm in-process index.",
        "retrieval": runs,
        "classifier": evaluate_classifier(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/latest.json")
    parser.add_argument("--semantic", action="store_true")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()
    report = run_evaluation(args.semantic, args.model)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Saved {report['question_count']} retrieval cases and {report['classifier']['test_examples']} classifier cases to {path}"
    )
