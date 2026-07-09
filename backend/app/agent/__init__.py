"""Paquete de agente para MediFlow.

Este paquete expone la implementación del agente, herramientas,
memoria, prompts y la ruta del endpoint /assistant.
"""

from .agent import run_agent_query
from .memory import build_agent_memory
from .prompts import (
    KNOWLEDGE_TOOL_DESCRIPTION,
    TRIAGE_TOOL_DESCRIPTION,
    PREDICT_NO_SHOW_TOOL_DESCRIPTION,
)
from .router import router
from .tools import build_agent_tools

__all__ = [
    "run_agent_query",
    "build_agent_tools",
    "build_agent_memory",
    "router",
    "KNOWLEDGE_TOOL_DESCRIPTION",
    "TRIAGE_TOOL_DESCRIPTION",
    "PREDICT_NO_SHOW_TOOL_DESCRIPTION",
]
