# Your A–Z path through SupportLens

The purpose is to finish with a project you can run, change, debug, and explain. Use each checkpoint as a milestone; do not rush through code you cannot yet describe.

## A. Run the first version

Follow the README setup, ask the returns question, inspect the citations, add one document, and run the benchmark. Learn where data is stored and how to stop and restart the app. Done means you can repeat the demonstration without help.

## B. Understand the request

Start at `frontend/src/api.ts`, then read `main.py`, `knowledge.py`, and `db.py`. Trace a question from the browser to the database. Open the interactive API documentation at `/docs` and send a question directly. Explain the difference between the interface, API, database, and AI components.

## C. Make your first change

Create your own fictional product with a useful support guide. Add five questions, including two that the guide cannot answer. Change a visible heading or add a category filter to the document library. Check that it still works on a narrow screen. Record your changes in a Git commit you understand.

## D. Learn retrieval

Read `retrieval.py`. Work through tokenization, TF-IDF, BM25, and reciprocal rank fusion. Change a chunk-size setting on a separate branch and measure what changes. Explain why longer context is not always better and why term overlap can return irrelevant evidence.

## E. Connect a language model

Install Ollama, download a model appropriate for your computer, and enable it in `.env`. Compare its generated answer to the default excerpts. Stop Ollama and confirm that the fallback is clearly labeled. Try an unrelated question, a request for an unsupported discount, and instructions embedded inside a document. Record failures without treating a prompt as a complete security boundary.

## F. Add and assess semantic retrieval

Enable the Sentence Transformers extra. Compare paraphrased questions and exact terminology. Keep lexical and semantic reports separate. Study a question where each method fails. Do not claim semantic search improves results unless your measured comparison supports it.

## G. Strengthen the ML component

Read `classifier.py` and inspect its training examples. Add a new category with a separate development set. Report macro F1 and a confusion matrix. Then obtain an independently sourced evaluation set; the bundled perfect score is an easy synthetic result, not proof of generalization.

## H. Test the product

Run `python -m pytest -q` and `pnpm build`. Read the integration tests: persistence, duplicate documents, file limits, citation integrity, model failures, and deleting a source. Add a test when you introduce a meaningful new behavior. Re-run the relevant checks after each change.

## I. Prepare GitHub

Follow `GITHUB_AND_RESUME.md`. Use screenshots, a short demo video, a reproducible setup, measured results, and a clear limitations section. Keep secrets, uploaded documents, local databases, downloaded models, and virtual environments out of the repository.

## J. Prepare for interviews

Practice a three-minute explanation: problem, users, architecture, one failure you found, one change you measured, and what you would improve. Be ready to open a function and explain it line by line. A useful first personal contribution is improving unknown-question handling on a new dataset.

## K. Deploy only when ready

The local edition deliberately binds to your own computer. Before public deployment, add login, per-user document boundaries, request limits, backup/retention rules, HTTPS, and persistent storage. Decide how model inference will run and what its actual cost and latency are. Test the container and PostgreSQL paths in the intended hosting environment. No hosting account or public repository was created for this local-first delivery.

## Good next contributions

- Add source-level filters and document update/version history.
- Improve unsupported-question handling, evaluated on fresh examples.
- Add a real independent ticket dataset and inspect mistakes by category.
- Add per-claim citation support review and compare reviewers.
- Add PostgreSQL migrations and verify persistence against a local instance.
- Add authenticated workspaces before a public deployment.

Choose one measurable change at a time. Keep a short experiment log describing the hypothesis, change, result, and limitation.
