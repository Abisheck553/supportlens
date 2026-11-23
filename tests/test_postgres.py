"""Optional live PostgreSQL check using a unique, disposable schema."""

import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from supportlens.config import Settings
from supportlens.main import create_app


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="PostgreSQL is tested in CI"
)
def test_postgres_document_and_conversation_lifecycle():
    url = make_url(os.environ["TEST_DATABASE_URL"])
    schema = "supportlens_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = url.update_query_dict({"options": f"-csearch_path={schema}"})
    settings = Settings(
        database_url=isolated.render_as_string(hide_password=False),
        seed_demo=False,
        enable_semantic=False,
        answer_provider="extractive",
    )
    try:
        with TestClient(create_app(settings)) as client:
            document = client.post(
                "/api/documents",
                json={
                    "title": "Penguin shipping",
                    "content": "Penguin shipping takes exactly seven working days.",
                },
            )
            assert document.status_code == 201
            response = client.post(
                "/api/questions",
                json={"question": "How long does penguin shipping take?"},
            )
            assert response.status_code == 200
            result = response.json()
            assert "seven" in result["answer"]
            assert (
                client.put(
                    f"/api/conversations/{result['id']}/feedback",
                    json={"feedback": "helpful"},
                ).status_code
                == 200
            )
        with TestClient(create_app(settings)) as client:
            assert client.get("/api/conversations").json()[0]["feedback"] == "helpful"
            assert (
                client.delete(f"/api/documents/{document.json()['id']}").status_code
                == 204
            )
            assert client.get("/api/documents").json() == []
            assert (
                client.delete(f"/api/conversations/{result['id']}").status_code == 204
            )
    finally:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
