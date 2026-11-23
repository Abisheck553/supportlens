import hashlib
import json
import re
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Chunk, Document

DATA_DIR = Path(__file__).parent / "data"


def read_fixture(name):
    return json.loads((DATA_DIR / name).read_text())


def chunk_text(text: str, size: int = 180, overlap: int = 30) -> list[str]:
    # Keep paragraphs intact where possible; overlap long paragraphs for continuity.
    parts, current = [], []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        words = paragraph.split()
        if not words:
            continue
        if len(words) > size:
            if current:
                parts.append("\n\n".join(current))
                current = []
            for start in range(0, len(words), size - overlap):
                parts.append(" ".join(words[start : start + size]))
                if start + size >= len(words):
                    break
        elif sum(len(p.split()) for p in current) + len(words) > size:
            parts.append("\n\n".join(current))
            current = [paragraph]
        else:
            current.append(paragraph)
    if current:
        parts.append("\n\n".join(current))
    return parts


def add_document(
    session: Session, title: str, content: str, filename: str = "pasted-text.md"
):
    normalized = content.replace("\x00", "").strip()
    if len(normalized.split()) < 5:
        raise ValueError("Add at least five words of readable document text.")
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    if session.scalar(select(Document).where(Document.digest == digest)):
        raise ValueError("This document is already in your knowledge base.")
    document = Document(
        id=str(uuid4()),
        title=title,
        filename=filename[:255],
        digest=digest,
        content=normalized,
    )
    document.chunks = [
        Chunk(id=str(uuid4()), position=i, text=text)
        for i, text in enumerate(chunk_text(normalized))
    ]
    session.add(document)
    session.commit()
    return document


def seed_documents(session: Session):
    if session.scalar(select(Document.id).limit(1)):
        return
    for item in read_fixture("documents.json"):
        add_document(session, item["title"], item["content"], item["filename"])


def corpus_from_session(session):
    return [
        {
            "id": c.id,
            "document_id": d.id,
            "title": d.title,
            "filename": d.filename,
            "position": c.position,
            "text": c.text,
        }
        for c, d in session.execute(
            select(Chunk, Document).join(Document).order_by(Document.id, Chunk.position)
        )
    ]


def demo_corpus():
    return [
        {
            "id": f"{d['filename']}:{i}",
            "document_id": d["filename"],
            "title": d["title"],
            "filename": d["filename"],
            "position": i,
            "text": text,
        }
        for d in read_fixture("documents.json")
        for i, text in enumerate(chunk_text(d["content"]))
    ]
