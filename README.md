# SupportLens

**An evidence-first customer support copilot you can run locally, inspect, and measure.**

Upload support documentation, ask a customer question, inspect the retrieved passages, and save feedback. The app includes a trained ticket classifier and a reproducible evaluation lab.

![SupportLens local interface](docs/screenshot.jpg)

## Start here

The delivered ZIP includes a built interface. Python 3.11 or newer is enough to run it; Node.js is only needed to change or rebuild the interface.

Open a terminal in the `supportlens` folder and run:

```sh
python3 scripts/setup.py
python3 scripts/run.py
```

Open **http://127.0.0.1:8000**. Press Ctrl+C in the terminal to stop. On Windows, use `python` instead of `python3`.

On the computer where this project was created, the Python environment and interface are already prepared. You can double-click **Start SupportLens.command** on macOS, or run just `python3 scripts/run.py`.

If port 8000 is already in use, run `python3 scripts/run.py --port 8001`.

For a fresh Git clone, install Node.js 22+ and pnpm 11.25.0, then run `python3 scripts/setup.py`; it will also install and build the frontend. Alternatively:

```sh
pnpm install --frozen-lockfile
pnpm build
python3 scripts/setup.py
python3 scripts/run.py
```

## Try it in five minutes

1. Ask **“Can I return an unused item after 20 days?”**
2. Select a citation and inspect its source passage.
3. Mark the answer helpful, then reopen it from Conversations.
4. Add your own Markdown, text, or text-based PDF through Add documents.
5. Open Evaluation lab and run the benchmark. Inspect the failures, too.

Eight fictional store policies are included as demo data. They are not policies of a real business. Uploaded documents and conversation history are saved in `data/supportlens.db` and excluded from Git.

The demo policies are inserted when the library is empty at startup. Set `SEED_DEMO=false` in `.env` if you want an empty library to stay empty.

## What is implemented

| Capability | Current implementation |
|---|---|
| Frontend | React, TypeScript, responsive layout, accessible forms and dialogs |
| Backend | FastAPI, request validation, interactive API docs at `/docs` |
| Storage | SQLite by default; SQLAlchemy supports a PostgreSQL connection |
| Ingestion | Text, Markdown, and readable PDF files; duplicate detection; overlapping chunks |
| Retrieval | BM25 baseline; BM25 + TF-IDF reciprocal rank fusion by default |
| Semantic retrieval | Optional Sentence Transformers embeddings, enabled separately |
| Default answers | Exact source excerpts, clearly labeled; no API key or language model required |
| Generated replies | Optional local Ollama integration, structured output and citation-reference validation |
| Ticket classification | TF-IDF + logistic regression; 60 synthetic training examples across five categories |
| Review | Saved source snapshots, conversation history, helpful/unhelpful feedback |
| Evaluation | 32 retrieval questions and 20 distinct classifier test examples; JSON export |
| Engineering | 24 backend tests, frontend type checking and build, CI workflow, Docker files |

**The default edition is a retrieval and classification application.** It becomes a generative RAG application when you connect a language model. Source references are validated, but that alone does not prove that a generated statement is supported by its citation.

## Add local AI-written replies

**One command (macOS):** run `python3 scripts/setup_ai.py`. It downloads the official Ollama runtime into `.runtime/` (checksum-verified), pulls `qwen3:4b-instruct`, downloads a pinned `all-MiniLM-L6-v2` embedding model, and writes the matching settings to `.env`. Then start the app with `python3 scripts/run.py --open`; it starts and stops the local model for you. Expect a few gigabytes of downloads. Model files stay in `.runtime/` and are never committed. Use `python3 scripts/run.py --no-ai` to go back to source-excerpt mode for one run.

**Manual setup (any OS):**

1. Install [Ollama](https://ollama.com/download) and start it.
2. Download a model suitable for your computer, for example `ollama pull qwen3:4b`. Model downloads can be several gigabytes.
3. Copy `.env.example` to `.env` and set:

```dotenv
ANSWER_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
```

4. Restart SupportLens and ask a question.

If the model is unavailable, slow, or returns malformed citations, the app explicitly falls back to source excerpts. It never reports those excerpts as a generated reply. The integration uses Ollama's [documented chat endpoint](https://docs.ollama.com/api/chat).

This path was run live with `qwen3:4b-instruct` on an Apple-silicon Mac: **14 of 14** generation checks passed ([report](reports/generation.json)), including four unanswerable questions where the app correctly declined. Median answer latency was about 1.7 seconds. The first run passed 12 of 14 ([report](reports/generation-first-run.json)); the two failures were a missing visible citation and a raw-document reply, fixed by one strict-citation retry. This is a 14-question synthetic smoke test, not a factuality score.

## Add semantic search

Activate the virtual environment, then install the optional dependency and set `.env`:

```sh
source .venv/bin/activate
python -m pip install -e '.[semantic]'
```

```dotenv
ENABLE_SEMANTIC=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

On Windows, activate with `.venv\Scripts\activate`. The first semantic query downloads the model and can take longer. Subsequent queries reuse it in the process. The implementation uses normalized sentence embeddings and cosine similarity, following the [Sentence Transformers documentation](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html).

The hybrid method then combines BM25 with embedding ranks instead of TF-IDF ranks. The semantic benchmark is recorded separately in [reports/semantic.json](reports/semantic.json) and summarised below.

## Measured baseline

The checked-in [report](reports/baseline.json) records a local run of the bundled synthetic benchmark. Latency depends on hardware and is not a production capacity claim.

| Metric | BM25 | BM25 + TF-IDF | BM25 + embeddings |
|---|---:|---:|---:|
| Recall @ 3, 24 answerable questions | 91.67% (22/24) | 91.67% (22/24) | **95.83% (23/24)** |
| Mean reciprocal rank @ 3 | 0.9167 | 0.9167 | **0.9583** |
| Abstention on 8 unanswerable questions | 50% | 50% | 50% |
| Mean retrieval latency (warm) | 0.3 ms | 0.3 ms | 5.5 ms |

The classifier scored 1.00 macro F1 on 20 hand-authored, held-out examples, compared with a 20% majority-class accuracy baseline. This tiny, easy dataset does **not** establish real-world accuracy. BM25 and BM25 + TF-IDF tie on this dataset. Semantic embeddings recover one extra question, which is a small gain on a small benchmark rather than proof of general improvement. Abstention on unanswerable questions is still the weakest area.

Known failures include a question about supported browsers being rejected and an unsupported student discount question retrieving subscription passages. These are retained in the report and UI. Retrieval success is not generated-answer correctness. See [evaluation methodology](docs/EVALUATION.md).

## Develop and test

```sh
source .venv/bin/activate
python -m pytest -q
PYTHONPATH=backend python -m supportlens.evaluate --output reports/latest.json
pnpm build
```

For frontend development, run the backend and Vite in separate terminals:

```sh
PYTHONPATH=backend .venv/bin/python -m uvicorn supportlens.main:create_app --factory --host 127.0.0.1 --port 8000 --reload
pnpm dev
```

Vite serves the UI on port 5173 and forwards `/api` to port 8000. Windows users can set `$env:PYTHONPATH="backend"` in PowerShell before running Python. `requirements.lock` and `pnpm-lock.yaml` record the installed dependencies.

## Project map

```text
backend/supportlens/
  main.py          API endpoints and app lifecycle
  db.py            SQLAlchemy models and database setup
  knowledge.py     Document ingestion and chunking
  retrieval.py     BM25, TF-IDF, optional embeddings, rank fusion
  answers.py       Exact excerpts, Ollama, citation validation
  classifier.py    Ticket model training and inference
  evaluate.py      Reproducible benchmark
  data/            Synthetic documents, questions, and ticket data
frontend/src/      React interface and typed API client
tests/            Backend and integration tests
docs/             Architecture, learning guide, evaluation, GitHub guidance
reports/          Checked-in retrieval, semantic, and generation results
scripts/          Setup and local launch helpers
```

## Containers and PostgreSQL

`docker compose up --build` packages the UI and backend and stores SQLite in a named volume. The port is bound to loopback. Docker was not available on the build machine, so the container recipe has not been executed here.

For an existing PostgreSQL instance, install `pip install -e '.[postgres]'` and set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/supportlens` in `.env`. This uses standard SQLAlchemy tables; it does **not** implement pgvector or database-side vector search. SQLite was integration-tested; PostgreSQL needs verification against your instance. Existing SQLite data is not automatically migrated.

## Current boundaries

- Single-user local application, without login, tenant separation, or a public hosting configuration. Add authentication and access controls before exposing it beyond your computer.
- Up to 100 documents, 5 MB per upload, 100 PDF pages, and 250,000 extracted characters per document. Scanned PDFs need OCR. Indexing is in-process and intended for small collections.
- No automatic customer messaging. All replies are reviewable drafts or source excerpts.
- The knowledge base and classifier are English-oriented. Search thresholds are heuristics, not calibrated confidence values.
- Deleting a document removes it from future searches. Prior conversations retain the quoted source snapshots until those conversations are deleted.
- The app has saved individual question/answer records, not multi-turn contextual conversation memory.
- The one-command AI setup downloads a macOS Ollama build; on Windows or Linux, install Ollama yourself. Docker and PostgreSQL still need their own environment validation.

Continue with the [A–Z learning guide](docs/LEARNING_GUIDE.md), [architecture](docs/ARCHITECTURE.md), and [GitHub and résumé guide](docs/GITHUB_AND_RESUME.md).

MIT licensed. All bundled sample policies and ticket examples are synthetic.
