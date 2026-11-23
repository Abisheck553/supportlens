import io
import json
from unittest.mock import Mock
import httpx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from supportlens.config import Settings
from supportlens.main import create_app
from supportlens.answers import answer_question
from supportlens.classifier import evaluate_classifier
from supportlens.knowledge import chunk_text, read_fixture
from supportlens.retrieval import Retriever


@pytest.fixture
def client(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path}/test.db",
            seed_demo=True,
            enable_semantic=False,
            answer_provider="extractive",
        )
    )
    with TestClient(app) as client:
        yield client


def test_seed_search_and_citation_integrity(client):
    assert client.get("/api/stats").json()["documents"] == 8
    response = client.post(
        "/api/questions",
        json={"question": "Can I return an unused item after 20 days?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sources"][0]["filename"] == "returns.md"
    assert "30 days" in body["answer"]
    assert body["mode"] == "extractive"
    assert body["needs_review"] is True
    for i in body["citation_ids"]:
        assert body["sources"][i - 1]["text"] in body["answer"]


def test_unknown_question_abstains(client):
    body = client.post(
        "/api/questions", json={"question": "What is the weather in Tokyo?"}
    ).json()
    assert body["mode"] == "insufficient_evidence"
    assert body["citation_ids"] == []
    assert body["sources"] == []


def test_document_lifecycle_updates_retrieval(client):
    created = client.post(
        "/api/documents",
        json={
            "title": "Lunar delivery",
            "content": "Lunar delivery is available only on Tuesdays. Moon packages require a silver delivery stamp.",
        },
    )
    assert created.status_code == 201
    document_id = created.json()["id"]
    result = client.post(
        "/api/questions", json={"question": "When is lunar delivery available?"}
    ).json()
    assert document_id in [s["document_id"] for s in result["sources"]]
    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    result = client.post(
        "/api/questions", json={"question": "When is lunar delivery available?"}
    ).json()
    assert document_id not in [s["document_id"] for s in result["sources"]]
    assert client.get(f"/api/documents/{document_id}").status_code == 404


def test_duplicate_and_blank_documents(client):
    doc = {
        "title": "A policy",
        "content": "The special orange voucher expires after exactly eleven months.",
    }
    assert client.post("/api/documents", json=doc).status_code == 201
    assert client.post("/api/documents", json=doc).status_code == 400
    assert (
        client.post(
            "/api/documents",
            json={"title": " ", "content": "enough words to pass the content check"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/documents", json={"title": "Empty", "content": "          "}
        ).status_code
        == 422
    )


def test_upload_text_and_reject_bad_inputs(client):
    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "../../sample.txt",
                b"Unicorn deliveries require a magical shipping permit.",
                "text/plain",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "sample.txt"
    assert (
        client.post(
            "/api/documents/upload",
            files={"file": ("script.html", b"<script>alert(1)</script>")},
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/documents/upload", files={"file": ("bad.txt", b"\xff\xfe\xfd")}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/documents/upload",
            files={"file": ("large.txt", b"x" * (5 * 1024 * 1024 + 1))},
        ).status_code
        == 413
    )


def test_blank_and_malformed_pdf_are_reported(client):
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    result = client.post(
        "/api/documents/upload",
        files={"file": ("scan.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert result.status_code == 400
    assert "OCR" in result.json()["detail"]
    assert (
        client.post(
            "/api/documents/upload", files={"file": ("bad.pdf", b"not a pdf")}
        ).status_code
        == 400
    )


def test_readable_pdf_upload(client):
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): writer._add_object(font)}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(
        b"BT /F1 12 Tf 50 750 Td (Penguin deliveries arrive on the second Monday of each month.) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    result = client.post(
        "/api/documents/upload",
        files={"file": ("penguins.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert result.status_code == 201
    stored = client.get("/api/documents/" + result.json()["id"]).json()
    assert "Penguin deliveries" in stored["content"]


def test_history_feedback_and_delete(client):
    result = client.post(
        "/api/questions", json={"question": "How do I reset my password?"}
    ).json()
    id = result["id"]
    assert (
        client.put(
            f"/api/conversations/{id}/feedback", json={"feedback": "helpful"}
        ).status_code
        == 200
    )
    assert client.get("/api/conversations").json()[0]["feedback"] == "helpful"
    assert client.get("/api/stats").json()["helpful"] == 1
    assert (
        client.put(
            f"/api/conversations/{id}/feedback", json={"feedback": "invalid"}
        ).status_code
        == 422
    )
    assert client.delete(f"/api/conversations/{id}").status_code == 204
    assert client.get("/api/conversations").json() == []


def test_persistence_and_empty_corpus(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/persist.db",
        seed_demo=False,
        answer_provider="extractive",
        enable_semantic=False,
    )
    with TestClient(create_app(settings)) as c:
        assert c.get("/api/documents").json() == []
        assert (
            c.post(
                "/api/questions", json={"question": "Any delivery information?"}
            ).json()["sources"]
            == []
        )
        c.post(
            "/api/documents",
            json={
                "title": "Persistence",
                "content": "The persistent purple voucher remains valid for exactly two years.",
            },
        )
    with TestClient(create_app(settings)) as c:
        assert c.get("/api/documents").json()[0]["title"] == "Persistence"
        assert len(c.get("/api/conversations").json()) == 1


@pytest.mark.parametrize(
    "body",
    [
        {"question": " " * 4},
        {"question": "a" * 2001},
        {"question": "Hello there", "method": "bad"},
    ],
)
def test_question_validation(client, body):
    assert client.post("/api/questions", json=body).status_code == 422


def test_chunks_preserve_all_words_and_bound_length():
    words = [f"word{i}" for i in range(450)]
    chunks = chunk_text(" ".join(words), size=100, overlap=20)
    assert all(len(c.split()) <= 100 for c in chunks)
    assert set(" ".join(chunks).split()) == set(words)
    assert chunks[0].split()[-20:] == chunks[1].split()[:20]


def test_semantic_retrieval_uses_real_vector_path_without_download():
    import numpy as np

    class FakeEmbedder:
        def encode(self, texts, normalize_embeddings=True):
            return np.array(
                [
                    [1.0, 0.0] if "parcel" in t or "shipping" in t else [0.0, 1.0]
                    for t in texts
                ]
            )

    retriever = Retriever(semantic=True)
    retriever._model = FakeEmbedder()
    corpus = [
        {"id": "a", "title": "shipping", "text": "Packages take five days"},
        {"id": "b", "title": "accounts", "text": "Passwords require twelve characters"},
    ]
    result = retriever.search("parcel arrival", corpus)
    assert result[0]["id"] == "a"
    assert result[0]["similarity"] == 1.0


def test_bm25_does_not_use_embedding_model():
    retriever = Retriever(semantic=True)

    class ForbiddenEmbedder:
        def encode(self, *args, **kwargs):
            raise AssertionError("The keyword baseline must not depend on embeddings")

    retriever._model = ForbiddenEmbedder()
    corpus = [
        {"id": "a", "title": "Shipping", "text": "Express shipping costs nine euros."}
    ]
    assert (
        retriever.search("Express shipping cost", corpus, method="bm25")[0]["id"] == "a"
    )


@pytest.fixture
def sources():
    return [{"text": "Returns are accepted within 30 days.", "title": "Returns"}]


def test_model_output_citations_validated(monkeypatch, sources):
    response = Mock()
    response.json.return_value = {
        "message": {
            "content": json.dumps(
                {
                    "answer": "You have 30 days [1].",
                    "citation_ids": [1],
                    "needs_review": False,
                }
            )
        }
    }
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: response)
    result = answer_question(
        "Return window?", sources, Settings(answer_provider="ollama")
    )
    assert result["mode"] == "ollama"
    assert result["needs_review"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {"answer": "A claim [99]", "citation_ids": [99], "needs_review": False},
        {
            "answer": "Missing inline evidence",
            "citation_ids": [1],
            "needs_review": False,
        },
        {"answer": None, "citation_ids": [1], "needs_review": False},
    ],
)
def test_invalid_model_output_falls_back(monkeypatch, sources, payload):
    response = Mock()
    response.json.return_value = {"message": {"content": json.dumps(payload)}}
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: response)
    result = answer_question(
        "Return window?", sources, Settings(answer_provider="ollama")
    )
    assert result["mode"] == "extractive_fallback"
    assert sources[0]["text"] in result["answer"]


def test_missing_inline_citation_is_repaired_once(monkeypatch, sources):
    responses = []
    for answer in ["You have 30 days.", "You have 30 days [1]."]:
        response = Mock()
        response.json.return_value = {
            "message": {
                "content": json.dumps(
                    {
                        "answer": answer,
                        "citation_ids": [1],
                        "needs_review": True,
                    }
                )
            }
        }
        responses.append(response)
    request = Mock(side_effect=responses)
    monkeypatch.setattr(httpx, "post", request)
    result = answer_question(
        "Return window?", sources, Settings(answer_provider="ollama")
    )
    assert result["mode"] == "ollama"
    assert result["answer"] == "You have 30 days [1]."
    assert request.call_count == 2


def test_model_unavailable_is_not_disguised(monkeypatch, sources):
    def fail(*a, **kw):
        raise httpx.ConnectError("unavailable")

    monkeypatch.setattr(httpx, "post", fail)
    assert (
        answer_question("Return window?", sources, Settings(answer_provider="ollama"))[
            "mode"
        ]
        == "extractive_fallback"
    )


def test_model_can_abstain_despite_retrieval(monkeypatch, sources):
    response = Mock()
    response.json.return_value = {
        "message": {
            "content": json.dumps(
                {
                    "answer": "Not enough information",
                    "citation_ids": [],
                    "needs_review": True,
                }
            )
        }
    }
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: response)
    assert (
        answer_question(
            "Lifetime warranty?", sources, Settings(answer_provider="ollama")
        )["mode"]
        == "insufficient_evidence"
    )


def test_classifier_split_and_quality():
    data = read_fixture("tickets.json")
    assert {r["text"] for r in data["train"]}.isdisjoint(
        r["text"] for r in data["test"]
    )
    result = evaluate_classifier()
    assert result["accuracy"] > result["majority_baseline_accuracy"]
    assert result["macro_f1"] >= 0.7


def test_evaluation_counts_and_independence(client):
    before = client.get("/api/stats").json()
    report = client.post("/api/evaluations").json()
    assert (
        report["question_count"]
        == report["answerable_count"] + report["unknown_count"]
        == 32
    )
    assert len(report["retrieval"]) == 2
    for run in report["retrieval"]:
        cases = run["cases"]
        expected = (
            sum(c["rank"] is not None for c in cases if c["expected_source"])
            / report["answerable_count"]
        )
        assert run["recall_at_3"] == round(expected, 4)
    assert client.get("/api/stats").json() == before
