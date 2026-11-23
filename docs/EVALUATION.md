# Evaluation methodology and limitations

## Retrieval benchmark

The dataset contains 24 answerable and 8 unanswerable hand-authored questions over eight fictional store policies. Each answerable question has one expected source filename. Both retrieval methods use the same corpus, limits, and relevance gate. The live uploaded document library is intentionally not part of this benchmark, so adding a document does not silently change the comparison.

- **Recall @ 3:** fraction of answerable questions whose expected document appears among the three retrieved passages, after deduplicating document filenames.
- **MRR @ 3:** average reciprocal rank of the expected source among those distinct retrieved documents, or zero when absent. At most three passages are retrieved; multiple passages from one document can reduce the number of distinct sources returned.
- **Unknown-question abstention:** fraction of unanswerable questions producing zero retrieved passages after the relevance gate.
- **Latency:** mean wall-clock time of each search after a warm-up query. Includes query transformation and ranking, not index construction, model generation, HTTP overhead, or a concurrency load test.

The report does not measure answer factuality, coverage of each claim, appropriateness of the customer reply, or quality under prompt injection. An LLM's structured citation IDs can all be valid while its text is wrong. Add separately reviewed question/answer cases before claiming generated-answer quality.

The baseline ties: 22/24 answerable questions found and 4/8 unknown questions rejected by each method. Two answerable cases and four unknown cases fail. The complete case list is retained in `reports/baseline.json`; the UI shows every case.

## Classification benchmark

The classifier fits TF-IDF and logistic regression only on 60 training examples. It evaluates on 20 different texts across five categories. The test texts are not used to fit the vectorizer or classifier. A fixed random seed makes model training reproducible.

The measured 100% test accuracy and 1.00 macro F1 are from a tiny synthetic set with obvious category vocabulary. The train/test authors and subject matter overlap. These scores should not be presented as production performance. The majority-class accuracy baseline is 20% because the test set is balanced.

## Improve the experiment responsibly

1. Collect consented or appropriately licensed examples from a new source and remove personal details.
2. Split by customer, document family, or time where relevant, rather than randomly splitting near-duplicate messages.
3. Keep a development set for thresholds and a separate final test set. Once you inspect this project's bundled failures, treat that benchmark as a development set for subsequent tuning.
4. Add paraphrases, compound questions, unsupported requests that share policy vocabulary, and contradictory or outdated documents.
5. Compare BM25, BM25 + TF-IDF, dense retrieval, and BM25 + dense retrieval under equal constraints.
6. Add reviewer judgments of answer correctness, supported claims, completeness, and appropriate abstention. Treat automated LLM judging as another model to validate.
7. Measure cold start, p50/p95 latency, memory, and concurrency separately; record model identifiers and dependency versions.

Run `PYTHONPATH=backend python -m supportlens.evaluate --output reports/latest.json`. Use `--semantic` only after installing the semantic extra. Save each experiment with its configuration and dataset version.

Background reference: [Hugging Face RAG evaluation cookbook](https://huggingface.co/learn/cookbook/rag_evaluation).
