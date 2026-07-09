from typing import Any

from app.services.assistant_agent import _build_agent_memory as _build_internal_agent_memory


def build_agent_memory(conversation: Any) -> Any:
    """Construye la memoria del agente a partir de la implementación interna."""
    return _build_internal_agent_memory(conversation)
