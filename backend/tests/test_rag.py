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


def test_assistant_endpoint_uses_openai_agent_when_auto_and_openai_key(monkeypatch):
    monkeypatch.setattr(assistant_agent.settings, "ai_provider", "auto")
    monkeypatch.setattr(assistant_agent.settings, "openai_api_key", "openai-test")
    monkeypatch.setattr(assistant_agent.settings, "roq_api_key", "roq-test")
    monkeypatch.setattr(assistant_agent, "LANGCHAIN_AVAILABLE", True)
    monkeypatch.setattr(assistant_agent, "AgentType", type("X", (), {"ZERO_SHOT_REACT_DESCRIPTION": "zero_shot_react_description"}))
    monkeypatch.setattr(assistant_agent, "_get_openai_llm", lambda: object())
    monkeypatch.setattr(assistant_agent, "_build_agent_memory", lambda conversation: None)
    monkeypatch.setattr(assistant_agent, "_build_agent_tools", lambda db: [])

    class DummyAgent:
        def run(self, question):
            return "openai agent response"

    monkeypatch.setattr(
        assistant_agent,
        "initialize_agent",
        lambda tools, llm, agent, memory, verbose, callbacks=None: DummyAgent(),
    )

    response = client.post("/assistant", json={"question": "¿Debo buscar atención médica urgente?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai"
    assert payload["answer"] == "openai agent response"
