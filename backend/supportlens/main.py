from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Literal
from uuid import uuid4
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from .answers import answer_question
from .classifier import classify
from .config import Settings
from .db import Chunk, Conversation, Document, create_database
from .evaluate import run_evaluation
from .knowledge import add_document, corpus_from_session, seed_documents
from .retrieval import Retriever


class DocumentInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=10, max_length=250_000)

    @field_validator("title", "content")
    @classmethod
    def not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class QuestionInput(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    method: Literal["bm25", "hybrid"] = "hybrid"

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter a question with at least three characters.")
        return value


class FeedbackInput(BaseModel):
    feedback: Literal["helpful", "unhelpful"]


def describe_document(document):
    return {
        "id": document.id,
        "title": document.title,
        "filename": document.filename,
        "chunk_count": len(document.chunks),
        "word_count": len(document.content.split()),
        "created_at": document.created_at.isoformat(),
    }


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    engine, Session = create_database(settings.database_url)
    retriever = Retriever(settings.enable_semantic, settings.embedding_model)

    @asynccontextmanager
    async def lifespan(app):
        if settings.seed_demo:
            with Session() as session:
                seed_documents(session)
        yield
        engine.dispose()

    app = FastAPI(
        title="SupportLens API",
        version="0.2.0",
        lifespan=lifespan,
        description="Single-user portfolio app. No authentication: bind locally or add access control before public deployment.",
    )
    app.state.session_factory = Session

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "answer_provider": settings.answer_provider,
            "retrieval_mode": "BM25 + sentence embeddings"
            if settings.enable_semantic
            else "BM25 + TF-IDF",
            "semantic_enabled": settings.enable_semantic,
            "model": settings.ollama_model
            if settings.answer_provider == "ollama"
            else None,
        }

    @app.get("/api/stats")
    def stats():
        with Session() as session:
            conversations = session.scalars(select(Conversation)).all()
            return {
                "documents": session.scalar(select(func.count()).select_from(Document)),
                "chunks": session.scalar(select(func.count()).select_from(Chunk)),
                "questions": len(conversations),
                "supported": sum(
                    bool(c.result.get("citation_ids")) for c in conversations
                ),
                "helpful": sum(c.feedback == "helpful" for c in conversations),
            }

    @app.get("/api/documents")
    def documents():
        with Session() as session:
            return [
                describe_document(d)
                for d in session.scalars(
                    select(Document).order_by(Document.created_at.desc())
                )
            ]

    def save_document(title, content, filename):
        if len(content) > 250_000:
            raise HTTPException(
                413, "Extracted text exceeds the 250,000-character limit."
            )
        with Session() as session:
            if session.scalar(select(func.count()).select_from(Document)) >= 100:
                raise HTTPException(
                    400, "This local edition supports up to 100 documents."
                )
            try:
                return describe_document(
                    add_document(session, title, content, filename)
                )
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            except IntegrityError as exc:
                session.rollback()
                raise HTTPException(
                    409, "This document is already in your knowledge base."
                ) from exc

    @app.post("/api/documents", status_code=201)
    def create_document(body: DocumentInput):
        return save_document(body.title, body.content, "pasted-text.md")

    @app.post("/api/documents/upload", status_code=201)
    def upload_document(file: UploadFile):
        filename = Path((file.filename or "document.txt").replace("\\", "/")).name
        suffix = Path(filename).suffix.lower()
        if suffix not in {".txt", ".md", ".pdf"}:
            raise HTTPException(
                415, "Upload a PDF, Markdown (.md), or plain-text (.txt) file."
            )
        contents = file.file.read(5 * 1024 * 1024 + 1)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(413, "Files must be 5 MB or smaller.")
        try:
            if suffix == ".pdf":
                reader = PdfReader(BytesIO(contents))
                if reader.is_encrypted:
                    raise ValueError("Remove the PDF password before uploading.")
                if len(reader.pages) > 100:
                    raise ValueError("PDFs must have 100 pages or fewer.")
                content = "\n\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                if len(content.strip()) < 10:
                    raise ValueError(
                        "No readable text found. Scanned PDFs need OCR first."
                    )
            else:
                content = contents.decode("utf-8-sig")
        except UnicodeError as exc:
            raise HTTPException(400, "Save text files with UTF-8 encoding.") from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                400, "This PDF could not be read. Try exporting it again."
            ) from exc
        return save_document(
            Path(filename).stem[:160] or "Untitled document", content, filename
        )

    @app.get("/api/documents/{document_id}")
    def get_document(document_id: str):
        with Session() as session:
            document = session.get(Document, document_id)
            if not document:
                raise HTTPException(404, "Document not found.")
            return {**describe_document(document), "content": document.content}

    @app.delete("/api/documents/{document_id}", status_code=204)
    def delete_document(document_id: str):
        with Session() as session:
            document = session.get(Document, document_id)
            if not document:
                raise HTTPException(404, "Document not found.")
            session.delete(document)
            session.commit()

    @app.post("/api/questions")
    def ask(body: QuestionInput):
        started = perf_counter()
        with Session() as session:
            corpus = corpus_from_session(session)
            try:
                sources = retriever.search(body.question, corpus, body.method)
            except (ImportError, OSError) as exc:
                raise HTTPException(
                    503,
                    "Semantic search is unavailable. Install the semantic extra and download the model, or set ENABLE_SEMANTIC=false.",
                ) from exc
            result = answer_question(body.question, sources, settings)
            result.update(
                {
                    "id": str(uuid4()),
                    "question": body.question,
                    "sources": sources,
                    "classification": classify(body.question),
                    "method": body.method,
                    "latency_ms": round((perf_counter() - started) * 1000, 2),
                    "feedback": None,
                }
            )
            session.add(
                Conversation(id=result["id"], question=body.question, result=result)
            )
            session.commit()
            return result

    @app.get("/api/conversations")
    def history():
        with Session() as session:
            return [
                {
                    **c.result,
                    "feedback": c.feedback,
                    "created_at": c.created_at.isoformat(),
                }
                for c in session.scalars(
                    select(Conversation)
                    .order_by(Conversation.created_at.desc())
                    .limit(100)
                )
            ]

    @app.delete("/api/conversations/{conversation_id}", status_code=204)
    def delete_conversation(conversation_id: str):
        with Session() as session:
            conversation = session.get(Conversation, conversation_id)
            if not conversation:
                raise HTTPException(404, "Conversation not found.")
            session.delete(conversation)
            session.commit()

    @app.put("/api/conversations/{conversation_id}/feedback")
    def feedback(conversation_id: str, body: FeedbackInput):
        with Session() as session:
            conversation = session.get(Conversation, conversation_id)
            if not conversation:
                raise HTTPException(404, "Conversation not found.")
            conversation.feedback = body.feedback
            session.commit()
            return {"id": conversation_id, "feedback": conversation.feedback}

    @app.post("/api/evaluations")
    def evaluate():
        try:
            return run_evaluation(settings.enable_semantic, settings.embedding_model)
        except (ImportError, OSError) as exc:
            raise HTTPException(
                503,
                "The embedding model is unavailable. Check the semantic model setup.",
            ) from exc

    dist = Path(__file__).resolve().parents[2] / "dist"
    # Installed packages may not share a source checkout. The launch script uses the project cwd.
    if not dist.is_dir():
        dist = Path.cwd() / "dist"
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/")
        def index():
            return FileResponse(dist / "index.html")

    return app


# uvicorn --factory supportlens.main:create_app keeps test imports side-effect free.
