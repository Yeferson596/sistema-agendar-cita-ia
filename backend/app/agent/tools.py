from typing import Any

from app.services.assistant_agent import _build_agent_tools as _build_internal_agent_tools


def build_agent_tools(db: Any) -> list[Any]:
    """Construye las herramientas de agente a partir de la implementación interna."""
    return _build_internal_agent_tools(db)
