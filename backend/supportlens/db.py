from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    filename: Mapped[str] = mapped_column(String(255))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    chunks: Mapped[list["Chunk"]] = relationship(
        cascade="all, delete-orphan", back_populates="document"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    document: Mapped[Document] = relationship(back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON)
    feedback: Mapped[str | None] = mapped_column(String(12), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


def create_database(url: str):
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            options["poolclass"] = StaticPool
        elif url.startswith("sqlite:///./"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(
                parents=True, exist_ok=True
            )
    engine = create_engine(url, **options)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)
