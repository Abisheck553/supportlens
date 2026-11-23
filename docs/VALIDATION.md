# Delivery validation

Checked on 23 November 2026, using Python 3.11 and Node.js 24 on macOS.

## Completed checks

- **24 automated backend tests passed** (one PostgreSQL test is skipped unless a database URL is provided). These cover seeded search, exact excerpt citations, unknown-question abstention, document creation and deletion, duplicate detection, text and PDF ingestion, upload limits, conversation persistence, feedback, request validation, chunk boundaries, an isolated embedding-vector path, malformed model outputs, model connection failures, classifier separation, and benchmark accounting.
- **TypeScript check and production frontend build passed.** The delivered `dist/` folder contains the built interface.
- **Browser workflow passed:** open the app, submit a sample question, inspect citations, save helpful feedback, revisit conversation history, add a pasted document, and run the evaluation lab.
- **Responsive review:** inspected the narrow phone layout and desktop layout. The phone page had no horizontal document overflow.
- **Setup and launch:** executed the included setup script into the project's own `.venv`; launched with the included run script; verified HTTP 200 for the app and its health endpoint.
- **Benchmark:** the checked-in JSON contains all 32 retrieval cases and 20 held-out classifier predictions, including unsuccessful cases.

The browser-check document was removed after verification. One sample conversation remains in the prepared local database as a demonstration. No local database or virtual environment is included in the ZIP or Git index.

## Local AI checks

- **Live generation:** `qwen3:4b-instruct` through a local Ollama runtime passed 14 of 14 synthetic generation checks (`reports/generation.json`), after a first run at 12 of 14 (`reports/generation-first-run.json`).
- **Semantic retrieval:** pinned `all-MiniLM-L6-v2` embeddings reached 23 of 24 recall@3, against 22 of 24 for the lexical methods (`reports/semantic.json`).

## Not yet verified in a live environment

- Docker image build, a PostgreSQL connection, or deployment to a hosting service. Docker and PostgreSQL are not running on this computer.
- Production load, multi-user isolation, or generated-answer factuality. This is a local single-user portfolio edition.

The test run emitted one dependency deprecation warning about Starlette's current HTTPX test transport. No test failed. Keep dependency upgrades and any needed test-client migration in a future maintenance change.
