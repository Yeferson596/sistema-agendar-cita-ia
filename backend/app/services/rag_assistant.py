import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

logger = logging.getLogger(__name__)

# Documentos de conocimiento
INTERNAL_DOC = Path(__file__).parent.parent / "data" / "internal_medical_knowledge.md"
EXTERNAL_DOC = Path(__file__).parent.parent / "data" / "external_medical_guidelines.md"


def _load_documents() -> Dict[str, str]:
    """Carga los documentos internos y externos."""
    docs = {}
    if INTERNAL_DOC.exists():
        docs["internal"] = INTERNAL_DOC.read_text(encoding="utf-8")
    if EXTERNAL_DOC.exists():
        docs["external"] = EXTERNAL_DOC.read_text(encoding="utf-8")
    return docs


def _retrieve_relevant_context(question: str, docs: Dict[str, str]) -> tuple[str, List[str]]:
    """Recupera contexto relevante de los documentos usando búsqueda simple por palabras clave."""
    question_lower = question.lower()
    context_parts = []
    sources = []

    # Palabras clave expandidas para búsqueda
    keywords = set()
    for word in question_lower.split():
        if len(word) > 2:  # Más corto para capturar más
            keywords.add(word)
    # Agregar sinónimos comunes
    if "urgente" in question_lower or "urgencia" in question_lower:
        keywords.update(["urgencia", "urgente", "emergencia", "rápida", "inmediata"])
    if "médica" in question_lower or "médico" in question_lower:
        keywords.update(["médica", "médico", "salud", "atención", "consulta"])
    if "buscar" in question_lower or "necesito" in question_lower:
        keywords.update(["buscar", "necesito", "requiero", "atención"])

    for doc_name, content in docs.items():
        lines = content.split('\n')
        relevant_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if not line_lower or line_lower.startswith('#'):  # Saltar headers y líneas vacías
                continue
            # Si la línea contiene alguna palabra clave
            if any(keyword in line_lower for keyword in keywords):
                relevant_lines.append(line.strip())
        if relevant_lines:
            context_parts.append(f"**{doc_name.upper()}:**\n" + '\n'.join(relevant_lines[:5]))  # Limitar a 5 líneas
            sources.append(doc_name)

    # Si no se encontró nada específico, incluir secciones generales
    if not context_parts:
        for doc_name, content in docs.items():
            lines = content.split('\n')
            general_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')][:3]
            if general_lines:
                context_parts.append(f"**{doc_name.upper()}:**\n" + '\n'.join(general_lines))
                sources.append(doc_name)

    context = '\n\n'.join(context_parts)
    return context, sources


def _generate_roq_response(question: str, context: str) -> str:
    """Genera respuesta usando Roq AI con el contexto proporcionado."""
    
    if not GROQ_AVAILABLE:
        logger.debug("Groq no instalado")
        return None
    
    if not settings.roq_api_key:
        logger.debug("ROQ_API_KEY no configurada")
        return None

    try:
        client = Groq(api_key=settings.roq_api_key)
        
        system_prompt = """
ERES ASISTENTE MÉDICO DE MEDIFLOW.
RESPONDES EXCLUSIVAMENTE SOBRE LO QUE APARECE EN EL CONTEXTO PROPORCIONADO.
NUNCA INVENTAS INFORMACIÓN.

✅ INSTRUCCIONES OBLIGATORIAS:
1. Responde SOLO usando la información que existe en el CONTEXTO
2. Responde en español claro, directo y natural
3. Dame recomendaciones concretas, no genericas
4. Si la pregunta es sobre síntomas, responde directamente que hacer
5. AL FINAL SIEMPRE agrega: "Para valoración personalizada consulta a un profesional médico"
6. NO menciones documentos, internos, externos ni fuentes, solo responde la pregunta
        """

        resp = client.chat.completions.create(
            model=settings.roq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"PREGUNTA: {question}\n\nCONTEXTO:\n{context}"}
            ],
            temperature=0.2,
            max_tokens=400,
            timeout=12
        )
        
        respuesta = resp.choices[0].message.content.strip()
        logger.info("✅ ROQ respondio correctamente")
        return respuesta
        
    except Exception as e:
        logger.debug("ROQ no disponible: %s", str(e))
        return None


def _summarize_context(context: str, max_sentences: int = 2) -> str:
    lines = [line.strip() for line in context.splitlines() if line.strip() and not line.startswith("**")]
    if not lines:
        return ""
    summary = " ".join(lines[:max_sentences])
    return summary


def _build_local_fallback(question: str, context: str, sources: List[str]) -> str:
    """Construye una respuesta local más directa usando el contexto y la intención de la pregunta."""
    question_lower = question.lower()
    context_lower = context.lower()

    if any(keyword in question_lower for keyword in ["urgente", "urgencia", "emergencia", "inmediata"]):
        urgent_items = []
        urgent_map = {
            "dolor de pecho": "dolor de pecho",
            "dificultad para respirar": "dificultad para respirar",
            "desmayo": "desmayo",
            "hemorragia": "hemorragia",
            "fiebre alta": "fiebre alta",
            "sangre": "sangrado",
            "respiración": "problemas respiratorios",
        }
        for keyword, label in urgent_map.items():
            if keyword in context_lower:
                urgent_items.append(label)

        if urgent_items:
            symptoms = ", ".join(dict.fromkeys(urgent_items))
            base_response = (
                f"Según los documentos relevantes ({', '.join(sources)}), los síntomas que más suelen requerir atención médica urgente incluyen {symptoms}. "
                "Te recomendamos consultar a un profesional de la salud de inmediato para una valoración precisa."
            )
        else:
            base_response = (
                f"Según los documentos relevantes ({', '.join(sources)}), algunos síntomas que requieren atención urgente son dolor de pecho, dificultad para respirar, desmayo y hemorragia. "
                "Si observas cualquiera de estos signos, consulta a un médico lo antes posible."
            )
        return base_response

    if any(keyword in question_lower for keyword in ["especialidades", "ofrece", "tiene", "servicios"]):
        if "especialidades comunes como medicina general" in context_lower:
            base_response = (
                "MediFlow ofrece especialidades comunes como Medicina General, Odontología, Pediatría, Cardiología y Traumatología. "
                "Si tienes síntomas específicos, puedes usar el servicio de triaje para identificar la opción más adecuada."
            )
            return base_response

    if any(keyword in question_lower for keyword in ["triaje", "clasifica", "clasificación", "urgencia"]):
        base_response = (
            f"El sistema de triaje de MediFlow utiliza el contexto interno y externo para clasificar síntomas por especialidad y urgencia. "
            "Esto ayuda a priorizar la atención y a sugerir la cita más adecuada según el cuadro del paciente."
        )
        return base_response

    summary = _summarize_context(context)
    if summary:
        return (
            f"Basado en los documentos relevantes encontrados ({', '.join(sources)}), esto puede ayudarte: {summary} "
            "Para una valoración personalizada, consulta a un profesional de la salud."
        )

    return (
        f"Según los documentos relevantes encontrados ({', '.join(sources)}), tu pregunta sobre salud requiere evaluación profesional. "
        "Te recomendamos consultar con un médico para una valoración adecuada."
    )


def _fallback_response(question: str, context: str, sources: List[str]) -> str:
    """Respuesta de fallback cuando no hay API key de Roq AI."""
    base_response = _build_local_fallback(question, context, sources)

    if not settings.roq_api_key:
        base_response += (
            "\n\nNota: Esta respuesta se genera localmente porque no se ha configurado ROQ_API_KEY. "
            "Para respuestas más personalizadas, configura la clave de API de Roq AI."
        )

    return base_response


def answer_question(question: str) -> Dict[str, Any]:
    """Responde a una pregunta usando RAG con documentos internos y externos."""
    docs = _load_documents()
    context, sources = _retrieve_relevant_context(question, docs)

    # PRIMERO USAMOS ROQ/GROQ SI ESTA DISPONIBLE
    if GROQ_AVAILABLE and bool(settings.roq_api_key):
        logger.info("✅ Intentando responder con ROQ/GROQ")
        answer = _generate_roq_response(question, context)
        if answer:
            logger.info("✅ Respuesta generada correctamente con ROQ")
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "context": context,
                "ai_provider": "groq"
            }

    # Fallback
    answer = _fallback_response(question, context, sources)
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "context": context,
    }