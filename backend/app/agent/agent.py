from typing import Any, Dict, Optional

from app.services.assistant_agent import run_agent_query as _run_internal_agent_query


def run_agent_query(db: Any, question: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Ejecuta la consulta del agente usando la implementación interna existente."""
    return _run_internal_agent_query(db, question, conversation_id=conversation_id)
