import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.crud import get_or_create_specialty
from app.models import AssistantConversation, AssistantMessage, Urgency
from app.services.no_show import predict_no_show
from app.services.rag_assistant import _load_documents, GROQ_AVAILABLE, answer_question
from app.services.roq_triage import perform_triage

logger = logging.getLogger(__name__)

# Optional LangChain imports.
try:
    from langchain.agents import AgentType, Tool, initialize_agent
    from langchain.chat_models import ChatOpenAI
    from langchain.docstore.document import Document
    from langchain.embeddings.openai import OpenAIEmbeddings
    from langchain.memory import CombinedMemory, ConversationSummaryMemory, VectorStoreRetrieverMemory
    from langchain.vectorstores.pgvector import PGVector
    from langchain.callbacks.base import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    AgentType = Tool = initialize_agent = ChatOpenAI = Document = OpenAIEmbeddings = None
    CombinedMemory = ConversationSummaryMemory = VectorStoreRetrieverMemory = PGVector = BaseCallbackHandler = None


if BaseCallbackHandler is not None:
    class ToolUsageHandler(BaseCallbackHandler):
        def __init__(self) -> None:
            self.tool_names: list[str] = []

        def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs) -> None:
            name = serialized.get("name")
            if name:
                self.tool_names.append(name)

        def on_tool_end(self, output: str, **kwargs) -> None:
            return None
else:
    ToolUsageHandler = None

# Cache de retriever para evitar reconstruir en cada petición.
_retriever_cache: Optional[Any] = None


def _parse_datetime_utc(value: str) -> datetime:
    if not value or not isinstance(value, str):
        raise ValueError("start_at debe ser una cadena ISO 8601")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _parse_predict_input(payload: str) -> Dict[str, Any]:
    try:
        data = json.loads(payload)
    except ValueError:
        data = {}
        patterns = {
            "specialty": r"specialty['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
            "urgency": r"urgency['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
            "start_at": r"start_at['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, payload, re.IGNORECASE)
            if match:
                data[key] = match.group(1)

    specialty = data.get("specialty")
    urgency = data.get("urgency")
    start_at = data.get("start_at")
    if not specialty or not urgency or not start_at:
        raise ValueError(
            "predict_no_show requiere JSON con specialty, urgency y start_at (ISO 8601)."
        )

    urgency_value = urgency.lower()
    if urgency_value not in {"low", "medium", "high"}:
        raise ValueError("urgency debe ser low, medium o high.")

    return {
        "specialty": specialty.strip(),
        "urgency": urgency_value,
        "start_at": _parse_datetime_utc(start_at),
    }


def _get_openai_llm():
    if not LANGCHAIN_AVAILABLE:
        raise RuntimeError("langchain no está instalado")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")
    return ChatOpenAI(temperature=0.0, model_name=settings.openai_model, openai_api_key=settings.openai_api_key)


def _build_pgvector_retriever() -> Optional[Any]:
    global _retriever_cache
    if _retriever_cache is not None:
        return _retriever_cache

    if not LANGCHAIN_AVAILABLE:
        logger.warning("LangChain no disponible; no se crea pgvector retriever")
        return None

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY no configurada; no se crea pgvector retriever")
        return None

    if not settings.database_url.startswith("postgres") and not settings.database_url.startswith("postgresql"):
        logger.warning("DATABASE_URL no es Postgres; pgvector no se inicializa")
        return None

    documents = []
    for source, text in _load_documents().items():
        documents.append(Document(page_content=text, metadata={"source": source}))

    if not documents:
        logger.warning("No hay documentos para inicializar el vector store")
        return None

    try:
        embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
        vectorstore = PGVector.from_documents(
            documents,
            embeddings,
            collection_name="mediflow_knowledge",
            table_name="assistant_knowledge",
            connection_string=settings.database_url,
        )
        _retriever_cache = vectorstore.as_retriever(search_kwargs={"k": 4})
        logger.info("pgvector retriever inicializado")
        return _retriever_cache
    except Exception as exc:
        logger.warning("Error inicializando pgvector: %s", exc)
        return None


def _save_conversation_message(db: Session, conversation_id: uuid.UUID, role: str, content: str) -> None:
    message = AssistantMessage(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()


def _get_or_create_conversation(db: Session, conversation_id: Optional[str]) -> AssistantConversation:
    if conversation_id:
        try:
            parsed_id = uuid.UUID(conversation_id)
            conversation = db.get(AssistantConversation, parsed_id)
            if conversation:
                return conversation
        except ValueError:
            logger.warning("conversation_id inválido: %s", conversation_id)

    conversation = AssistantConversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def _populate_memory_from_db(conversation: AssistantConversation, memory: Any) -> None:
    if not conversation or not conversation.messages:
        return
    sorted_messages = sorted(conversation.messages, key=lambda msg: msg.created_at)
    pending_input = None
    for item in sorted_messages:
        if item.role == "user":
            pending_input = item.content
        elif item.role == "assistant" and pending_input is not None:
            memory.save_context({"input": pending_input}, {"output": item.content})
            pending_input = None


def _build_agent_memory(conversation: AssistantConversation) -> Any:
    llm = _get_openai_llm()
    summary_memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        input_key="input",
        output_key="output",
    )
    _populate_memory_from_db(conversation, summary_memory)

    retriever = _build_pgvector_retriever()
    if retriever is None:
        return summary_memory

    try:
        retriever_memory = VectorStoreRetrieverMemory(
            retriever=retriever,
            memory_key="knowledge",
            input_key="input",
        )
        combined = CombinedMemory(memories=[summary_memory, retriever_memory])
        return combined
    except Exception as exc:
        logger.warning("No se pudo combinar memoria de LangChain: %s", exc)
        return summary_memory


def _build_agent_tools(db: Session) -> list[Any]:
    tools: list[Any] = []

    def _triage_tool(question: str) -> str:
        result = perform_triage(question)
        return json.dumps(result, ensure_ascii=False)

    def _predict_tool(payload: str) -> str:
        parsed = _parse_predict_input(payload)
        specialty_obj = get_or_create_specialty(db, parsed["specialty"])
        urgency = Urgency(parsed["urgency"])
        risk, reasoning, features = predict_no_show(
            db,
            patient_id=uuid.UUID(int=0),
            specialty_id=specialty_obj.id,
            urgency=urgency,
            start_at=parsed["start_at"],
        )
        return json.dumps(
            {
                "no_show_risk": round(risk, 4),
                "reasoning": reasoning,
                "features": features,
            },
            ensure_ascii=False,
        )

    retriever = _build_pgvector_retriever()
    if retriever:
        def _knowledge_tool(query: str) -> str:
            docs = retriever.get_relevant_documents(query)
            if not docs:
                return "No se encontraron documentos relevantes en la memoria de conocimiento."
            return "\n\n".join(
                f"[{doc.metadata.get('source', 'unknown')}] {doc.page_content}" for doc in docs[:4]
            )

        tools.append(
            Tool(
                name="knowledge_search",
                func=_knowledge_tool,
                description=(
                    "Busca información médica relevante en la memoria de conocimiento RAG. "
                    "Entrada: pregunta del paciente. Salida: texto con fragmentos relevantes "
                    "y fuentes."
                ),
            )
        )

    tools.append(
        Tool(
            name="triage",
            func=_triage_tool,
            description=(
                "Clasifica síntomas y determina especialidad y urgencia. "
                "Entrada: descripción del cuadro clínico. Salida: JSON con specialty, urgency y reasoning."
            ),
        )
    )
    tools.append(
        Tool(
            name="predict_no_show",
            func=_predict_tool,
            description=(
                "Calcula el riesgo de no-show para una cita. "
                "Entrada: JSON con specialty, urgency y start_at (ISO). "
                "Salida: JSON con no_show_risk, reasoning y features."
            ),
        )
    )

    return tools


def run_agent_query(db: Session, question: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    use_roq = settings.ai_provider in ("roq", "auto") and bool(settings.roq_api_key) and GROQ_AVAILABLE
    use_openai = settings.ai_provider in ("openai", "auto") and bool(settings.openai_api_key)

    if use_roq:
        response = answer_question(question)
        return {
            "question": question,
            "answer": response["answer"],
            "sources": response.get("sources", []),
            "context": response.get("context"),
            "conversation_id": str(uuid.uuid4()),
            "used_tools": [],
            "provider": "roq",
        }

    if not LANGCHAIN_AVAILABLE or not use_openai:
        response = answer_question(question)
        return {
            "question": question,
            "answer": response["answer"],
            "sources": response.get("sources", []),
            "context": response.get("context"),
            "conversation_id": str(uuid.uuid4()),
            "used_tools": [],
            "provider": "fallback",
        }

    conversation = _get_or_create_conversation(db, conversation_id)
    memory = _build_agent_memory(conversation)
    llm = _get_openai_llm()
    tools = _build_agent_tools(db)

    tool_usage = ToolUsageHandler() if BaseCallbackHandler is not None else None

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        callbacks=[tool_usage] if tool_usage is not None else None,
    )
    answer = agent.run(question)

    _save_conversation_message(db, conversation.id, "user", question)
    _save_conversation_message(db, conversation.id, "assistant", answer)

    result: Dict[str, Any] = {
        "question": question,
        "answer": answer,
        "sources": [],
        "context": None,
        "conversation_id": str(conversation.id),
        "used_tools": tool_usage.tool_names if tool_usage is not None else [tool.name for tool in tools],
        "provider": "openai",
    }

    # Extra: recuperar contexto desde memoria de vectores si está disponible.
    retriever = _build_pgvector_retriever()
    if retriever:
        docs = retriever.get_relevant_documents(question)
        result["sources"] = [doc.metadata.get("source", "unknown") for doc in docs[:4]]
        result["context"] = "\n\n".join(doc.page_content for doc in docs[:4])
    return result
