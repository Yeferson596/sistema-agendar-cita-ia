import json
import logging
from typing import Any, Dict

from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class TriageSchema(BaseModel):
    specialty: str
    urgency: str
    reasoning: str


def _normalize_urgency(raw: str) -> str:
    u = (raw or "medium").strip().lower()
    if u in ("low", "medium", "high"):
        return u
    if u in ("baja", "bajo"):
        return "low"
    if u in ("alta", "alto", "critica", "crítica"):
        return "high"
    return "medium"


def _describe_reasoning(description: str, specialty: str, urgency: str) -> str:
    text = description.lower()
    if specialty == "Odontología":
        if any(w in text for w in ("sangre", "encía", "dolor de muelas", "muela", "diente")):
            return "Parece un problema dental o una infección de muela/encía que requiere atención odontológica rápida."
        return "Tus síntomas bucales sugieren una consulta odontológica para revisar la boca o las encías."
    if specialty == "Cardiología":
        return "Parece un malestar cardíaco o de presión en el pecho; conviene valoración cardiológica urgente."
    if specialty == "Traumatología":
        return "Tus síntomas muestran una posible lesión musculoesquelética o trauma; se sugiere revisión en Traumatología."
    if specialty == "Pediatría":
        if any(w in text for w in ("fiebre", "tos", "vómito", "diarrea")):
            return "Síntomas infantiles que podrían corresponder a una infección o malestar de crecimiento; consulta con pediatría."
        return "Síntomas de un menor que deben ser revisados por un especialista en pediatría."

    if any(w in text for w in ("gripe", "covid", "bronquitis", "neumonía")):
        return "Los síntomas parecen una infección respiratoria como gripe o bronquitis; conviene valoración médica."
    if any(w in text for w in ("tos", "resfriado", "mocos", "congestión", "dolor de garganta", "fiebre baja")):
        return "Parece una infección respiratoria leve o resfriado; conviene valoración en Medicina General."
    if any(w in text for w in ("fiebre", "escalofrío", "calentura", "sudoración")):
        return "Sospecha de infección con fiebre; se recomienda revisión de Medicina General para descartar un cuadro infeccioso."
    if any(w in text for w in ("diarrea", "vómito", "dolor abdominal", "náuseas", "náusea", "cólico")):
        return "Tus síntomas digestivos parecen una gastroenteritis o malestar estomacal; revisa con Medicina General."
    if any(w in text for w in ("dolor de cabeza", "migraña", "cefalea", "jaqueca")):
        return "Esto se asemeja a un cuadro de cefalea o migraña; se sugiere valoración médica general."
    if any(w in text for w in ("mareo", "vértigo", "desmayo", "debilidad", "fatiga")):
        return "Síntomas de mareo o debilidad que merecen valoración en Medicina General."
    if any(w in text for w in ("erupción", "picazón", "sarpullido", "alergia", "roncha")):
        return "Parece una reacción cutánea o alergia; conviene revisión médica para identificar la causa."
    if any(w in text for w in ("dolor al orinar", "ardor", "orina turbia", "infección urinaria")):
        return "Tus síntomas son compatibles con una infección urinaria; consulta en Medicina General para tratamiento."

    symptom = None
    for candidate in (
        "dolor", "malestar", "fatiga", "náuseas", "mareo", "tos", "fiebre", "inflamación", "hinchazón", "picor", "ardor",
        "cansancio", "dolor abdominal", "dolor de espalda", "dolor en el pecho", "dolor de garganta"
    ):
        if candidate in text:
            symptom = candidate
            break

    if symptom:
        return f"Tus síntomas de {symptom} sugieren consulta en Medicina General para determinar la causa exacta."

    return "Tus síntomas sugieren una consulta en Medicina General para determinar el problema exacto."


def _fallback_triage(description: str) -> Dict[str, Any]:
    text = description.lower()
    urgency = "medium"
    if any(w in text for w in ("dolor intenso", "sangre", "no puedo respirar", "emergencia", "desmayo", "ataque", "fiebre alta")):
        urgency = "high"
    elif any(w in text for w in ("control", "revisión", "consulta rutinaria", "chequeo", "seguimiento")):
        urgency = "low"
    specialty = "Medicina General"
    if any(w in text for w in ("muela", "diente", "encía", "boca", "gingivitis", "dolor de muelas")):
        specialty = "Odontología"
    elif any(w in text for w in ("niño", "bebé", "pediatr", "lactante", "pediátrico")):
        specialty = "Pediatría"
    elif any(w in text for w in ("corazón", "pecho", "presión", "taquicardia", "palpitaciones", "infarto")):
        specialty = "Cardiología"
    elif any(w in text for w in ("hueso", "articulación", "rodilla", "torcedura", "esguince", "fractura")):
        specialty = "Traumatología"
    reasoning = _describe_reasoning(description, specialty, urgency)
    return {
        "specialty": specialty,
        "urgency": urgency,
        "reasoning": reasoning,
    }


def _generate_openai_triage(description: str) -> Dict[str, Any]:
    try:
        import openai
    except ImportError as exc:
        raise RuntimeError("OpenAI package no instalado") from exc

    openai.api_key = settings.openai_api_key
    prompt = (
        "Analiza el malestar del paciente y devuelve JSON con specialty (nombre corto), "
        "urgency (solo: low, medium, high) y reasoning breve en español.\n\n"
        f"Paciente: \"{description}\""
    )

    response = openai.ChatCompletion.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "Eres un asistente de triaje médico. Clasifica en una especialidad (Pediatría, Odontología, Medicina General, Cardiología, Traumatología, etc.) y nivel de urgencia."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=250,
    )

    message = response.choices[0].message
    if isinstance(message, dict):
        text = message.get("content", "")
    else:
        text = getattr(message, "content", "")
    raw = text.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]

    data = json.loads(raw)
    parsed = TriageSchema.model_validate(data)
    u = _normalize_urgency(parsed.urgency)
    return {"specialty": parsed.specialty.strip(), "urgency": u, "reasoning": parsed.reasoning.strip()}


def perform_triage(description: str) -> Dict[str, Any]:
    use_openai = settings.ai_provider in ("openai", "auto") and bool(settings.openai_api_key)
    use_gemini = settings.ai_provider in ("gemini", "auto") and bool(settings.gemini_api_key)

    if use_openai:
        try:
            return _generate_openai_triage(description)
        except Exception as e:
            logger.warning("OpenAI triage failed: %s", e)

    if use_gemini:
        try:
            from google import genai
            from google.genai import types

            class TriageJsonModel(BaseModel):
                specialty: str
                urgency: str
                reasoning: str

            client = genai.Client(api_key=settings.gemini_api_key)
            model = settings.gemini_model
            resp = client.models.generate_content(
                model=model,
                contents=(
                    f'Analiza el malestar del paciente y devuelve JSON con specialty (nombre corto), '
                    f'urgency (solo: low, medium, high) y reasoning breve en español.\n\nPaciente: "{description}"'
                ),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Eres un asistente de triaje médico. Clasifica en una especialidad "
                        "(Pediatría, Odontología, Medicina General, Cardiología, Traumatología, etc.) "
                        "y nivel de urgencia."
                    ),
                    response_mime_type="application/json",
                    response_schema=TriageJsonModel,
                ),
            )
            text = (resp.text or "").strip()
            data = json.loads(text)
            parsed = TriageSchema.model_validate(data)
            u = _normalize_urgency(parsed.urgency)
            return {"specialty": parsed.specialty.strip(), "urgency": u, "reasoning": parsed.reasoning.strip()}
        except Exception as e:
            logger.warning("Gemini triage failed: %s", e)
            return _fallback_triage(description)
