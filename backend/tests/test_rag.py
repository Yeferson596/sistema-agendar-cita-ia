import os

from fastapi.testclient import TestClient

from app.main import app
from app.services import assistant_agent

client = TestClient(app)


def test_assistant_endpoint_returns_fallback_when_no_openai_key(monkeypatch):
    monkeypatch.setattr(assistant_agent.settings, "openai_api_key", "")

    response = client.post("/assistant", json={"question": "¿Debo buscar atención médica urgente?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "¿Debo buscar atención médica urgente?"
    assert "Esta respuesta se genera localmente" in payload["answer"]
    assert isinstance(payload["sources"], list)
    assert isinstance(payload["context"], str)
    assert payload["context"].strip()
