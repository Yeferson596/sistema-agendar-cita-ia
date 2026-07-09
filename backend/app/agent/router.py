from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.agent import run_agent_query
from app.database import get_db
from app.schemas import AgentQuery, AgentResponse

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("", response_model=AgentResponse)
def assist(
    query: AgentQuery,
    db: Annotated[Session, Depends(get_db)],
):
    result = run_agent_query(db, query.question, conversation_id=query.session_id)
    return AgentResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result.get("sources", []),
        context=result.get("context"),
        session_id=result["conversation_id"],
        used_tools=result.get("used_tools"),
        provider=result.get("provider"),
    )
