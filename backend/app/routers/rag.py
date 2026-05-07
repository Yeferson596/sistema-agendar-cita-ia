from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_assistant import answer_question

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantQuery(BaseModel):
    question: str


class AssistantResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    context: str


@router.post("", response_model=AssistantResponse)
def assist(query: AssistantQuery):
    return answer_question(query.question)
