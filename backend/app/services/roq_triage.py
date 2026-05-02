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
    
    # Razonamientos específicos por especialidad
    if specialty == "Odontología":
        if any(w in text for w in ("sangre", "encía", "dolor de muelas", "muela", "diente")):
            return "Parece un problema dental o una infección de muela/encía que requiere atención odontológica rápida."
        if any(w in text for w in ("caries", "picadura")):
            return "Síntomas de caries dental que necesitan revisión y tratamiento en odontología."
        return "Tus síntomas bucales sugieren una consulta odontológica para revisar la boca o las encías."
    
    if specialty == "Cardiología":
        if any(w in text for w in ("dolor en el pecho", "opresión", "angina")):
            return "Parece un malestar cardíaco o de presión en el pecho; conviene valoración cardiológica urgente."
        if any(w in text for w in ("taquicardia", "palpitaciones")):
            return "Síntomas de taquicardia o palpitaciones que requieren valoración cardiológica."
        return "Parece una afección cardiaca; se recomienda evaluación cardiológica."
    
    if specialty == "Traumatología":
        if any(w in text for w in ("fractura", "hueso roto")):
            return "Síntomas compatibles con fractura ósea; requiere evaluación y posible inmovilización en traumatología."
        if any(w in text for w in ("esguince", "torcedura")):
            return "Parece un esguince o torcedura; se sugiere revisión en traumatología para descartar lesiones graves."
        return "Tus síntomas muestran una posible lesión musculoesquelética o trauma; se sugiere revisión en Traumatología."
    
    if specialty == "Pediatría":
        if any(w in text for w in ("fiebre", "tos", "vómito", "diarrea")):
            return "Síntomas infantiles que podrían corresponder a una infección o malestar de crecimiento; consulta con pediatría."
        return "Síntomas de un menor que deben ser revisados por un especialista en pediatría."
    
    if specialty == "Dermatología":
        if any(w in text for w in ("alergia", "alérgico")):
            return "Reacción alérgica en la piel que requiere evaluación dermatológica para identificar el alérgeno."
        if any(w in text for w in ("erupción", "sarpullido", "roncha")):
            return "Erupción o sarpullido que sugiere dermatitis u otra afección dermatológica; necesita valoración."
        return "Síntomas cutáneos que requieren evaluación dermatológica especializada."
    
    if specialty == "Gastroenterología":
        if any(w in text for w in ("diarrea", "vómito", "dolor abdominal", "náuseas")):
            return "Tus síntomas digestivos parecen una gastroenteritis o malestar estomacal; revisa con especialista en gastroenterología."
        if any(w in text for w in ("reflujo", "acidez")):
            return "Síntomas de reflujo ácido o gastritis; se recomienda valoración gastroenterológica."
        return "Síntomas gastrointestinales que requieren evaluación especializada."
    
    if specialty == "Otorrinolaringología":
        if any(w in text for w in ("garganta", "faringitis", "amígdala")):
            return "Inflamación de garganta o faringitis que requiere evaluación ORL."
        if any(w in text for w in ("oído", "otitis", "dolor de oído")):
            return "Síntomas de otitis u otra afección del oído que necesita valoración especializada."
        return "Síntomas de oído, nariz o garganta que requieren evaluación ORL."
    
    if specialty == "Oftalmología":
        if any(w in text for w in ("conjuntivitis", "ojo rojo")):
            return "Síntomas de conjuntivitis que requieren valoración oftalmológica y posible tratamiento."
        if any(w in text for w in ("visión borrosa", "visión", "vista")):
            return "Problemas visuales que necesitan evaluación oftalmológica."
        return "Síntomas oculares que requieren revisión especializada."
    
    if specialty == "Neumonología":
        if any(w in text for w in ("bronquitis", "neumonía")):
            return "Síntomas de infección respiratoria (bronquitis o neumonía) que requieren valoración neumonológica."
        if any(w in text for w in ("asma", "asmático")):
            return "Síntomas de asma o crisis asmática que necesitan evaluación y tratamiento especializado."
        if any(w in text for w in ("tos persistente", "tos prolongada")):
            return "Tos persistente que sugiere una afección pulmonar; requiere valoración neumonológica."
        return "Síntomas respiratorios que requieren evaluación especializada."
    
    if specialty == "Neurología":
        if any(w in text for w in ("migraña", "cefalea", "jaqueca", "dolor de cabeza")):
            return "Esto se asemeja a un cuadro de cefalea o migraña; se sugiere valoración neurológica."
        if any(w in text for w in ("vértigo", "mareo", "desmayo")):
            return "Síntomas de vértigo o mareo que pueden corresponder a un trastorno neurológico; requiere evaluación."
        return "Síntomas neurológicos que requieren valoración especializada."
    
    if specialty == "Endocrinología":
        if any(w in text for w in ("diabetes", "azúcar en sangre")):
            return "Síntomas compatibles con diabetes u otro trastorno endocrino; requiere evaluación especializada."
        if any(w in text for w in ("tiroides", "hormona")):
            return "Síntomas que sugieren un trastorno de la tiroides u hormonal; necesita valoración endocrinológica."
        return "Síntomas que sugieren un trastorno endocrino; requiere evaluación especializada."
    
    if specialty == "Nefrología":
        if any(w in text for w in ("riñón", "infección urinaria", "cálculo")):
            return "Síntomas renales o urinarios que requieren valoración nefrológica especializada."
        return "Síntomas del sistema urinario que requieren evaluación especializada."
    
    # Razonamientos genéricos para Medicina General
    if any(w in text for w in ("gripe", "covid", "bronquitis")):
        return "Los síntomas parecen una infección respiratoria como gripe o bronquitis; conviene valoración médica."
    if any(w in text for w in ("tos", "resfriado", "mocos", "congestión", "dolor de garganta", "fiebre baja")):
        return "Parece una infección respiratoria leve o resfriado; conviene valoración en Medicina General."
    if any(w in text for w in ("fiebre", "escalofrío", "calentura", "sudoración")):
        return "Sospecha de infección con fiebre; se recomienda revisión de Medicina General para descartar un cuadro infeccioso."
    
    # Buscar síntomas generales
    symptom = None
    for candidate in (
        "dolor intenso", "dolor muy fuerte",
        "malestar", "fatiga", "náuseas", "mareo", "tos", "fiebre", 
        "inflamación", "hinchazón", "picor", "ardor",
        "cansancio", "dolor abdominal", "dolor de espalda", 
        "dolor en el pecho", "dolor de garganta"
    ):
        if candidate in text:
            symptom = candidate
            break

    if symptom:
        if urgency == "high":
            return f"Tus síntomas de {symptom} son graves y requieren atención médica inmediata."
        else:
            return f"Tus síntomas de {symptom} sugieren consulta en Medicina General para determinar la causa exacta."

    return "Tus síntomas sugieren una consulta en Medicina General para determinar el problema exacto."


def _fallback_triage(description: str) -> Dict[str, Any]:
    text = description.lower()
    
    # Determinar urgencia de forma más precisa
    urgency = "medium"
    
    # Palabras clave para urgencia ALTA
    high_urgency_keywords = [
        "dolor intenso", "dolor muy fuerte", "dolor insoportable",
        "sangre", "sangrado", "hemorragia",
        "no puedo respirar", "ahogo", "falta de aire",
        "emergencia", "urgencia",
        "desmayo", "desvanecimiento", "perdi el conocimiento",
        "ataque", "crisis",
        "fiebre alta", "fiebre muy alta",
        "vomito de sangre", "heces con sangre",
        "dolor en el pecho", "opresión en el pecho",
        "convulsión", "espasmo",
        "parálisis", "entumecimiento",
        "confusión mental", "desorientación"
    ]
    
    # Palabras clave para urgencia BAJA
    low_urgency_keywords = [
        "control", "revisión", "consulta rutinaria", "chequeo", "seguimiento",
        "molestia leve", "incomodidad",
        "picazón", "rasguño",
        "consejo", "consulta preventiva",
        "control periódico"
    ]
    
    if any(kw in text for kw in high_urgency_keywords):
        urgency = "high"
    elif any(kw in text for kw in low_urgency_keywords):
        urgency = "low"
    
    # Detectar especialidades con criterios más específicos
    specialty = "Medicina General"
    
    # Odontología
    if any(w in text for w in ("muela", "diente", "encía", "boca", "gingivitis", "dolor de muelas", "caries", "ortodon", "dental", "ortodancia")):
        specialty = "Odontología"
    # Pediatría
    elif any(w in text for w in ("niño", "bebé", "pediatr", "lactante", "pediátrico", "infante", "menor de edad", "hijo")):
        specialty = "Pediatría"
    # Cardiología
    elif any(w in text for w in ("corazón", "pecho", "presión arterial", "taquicardia", "palpitaciones", "infarto", "angina", "arritmia", "cardíaco")):
        specialty = "Cardiología"
    # Traumatología
    elif any(w in text for w in ("hueso", "articulación", "rodilla", "torcedura", "esguince", "fractura", "trauma", "golpe", "caída", "músculo", "tendón", "ligamento")):
        specialty = "Traumatología"
    # Dermatología
    elif any(w in text for w in ("erupción", "sarpullido", "picazón", "alergia", "roncha", "piel", "dermatitis", "eccema", "psoriasis", "lunar")):
        specialty = "Dermatología"
    # Gastroenterología
    elif any(w in text for w in ("diarrea", "vómito", "dolor abdominal", "náuseas", "cólico", "estómago", "intestino", "reflujo", "gastritis", "colon")):
        specialty = "Gastroenterología"
    # Otorrinolaringología
    elif any(w in text for w in ("oído", "nariz", "garganta", "sinusitis", "faringitis", "otitis", "sordera", "voz ronca", "laringitis")):
        specialty = "Otorrinolaringología"
    # Oftalmología
    elif any(w in text for w in ("ojo", "visión", "vista", "catarata", "glaucoma", "conjuntivitis", "miopía", "astigmatismo", "lagaña")):
        specialty = "Oftalmología"
    # Neumonología
    elif any(w in text for w in ("pulmón", "bronquitis", "neumonía", "asma", "tos seca", "tos persistente", "respiración", "disnea", "enfisema", "tuberculosis", "dificultad para respirar", "falta de aire", "ahogo")):
        specialty = "Neumonología"
    # Neurología
    elif any(w in text for w in ("cabeza", "migraña", "cefalea", "jaqueca", "vértigo", "mareo", "epilepsia", "nervio", "parestesia", "neuropatía")):
        specialty = "Neurología"
    # Endocrinología
    elif any(w in text for w in ("diabetes", "tiroides", "metabolismo", "hormona", "azúcar en sangre", "glucosa", "obesidad")):
        specialty = "Endocrinología"
    # Nefrología
    elif any(w in text for w in ("riñón", "orina", "infección urinaria", "cálculo", "nefritis", "insuficiencia renal")):
        specialty = "Nefrología"
    
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


def _generate_roq_triage(description: str) -> Dict[str, Any]:
    try:
        from groq import Groq

        client = Groq(api_key=settings.roq_api_key)
        
        system_prompt = """
Eres un médico especialista en triaje profesional. ANALIZA DETALLADAMENTE LOS SÍNTOMAS DEL PACIENTE Y SE MUY PRECISO.

CLASIFICA CON PRECISIÓN:
✅ SELECCIONA LA ESPECIALIDAD MÉDICA CORRECTA EXACTAMENTE SEGÚN LOS SÍNTOMAS
✅ DETERMINA LA URGENCIA REAL CON EVALUACIÓN CLÍNICA:
  - 🔴 HIGH: síntomas graves que requieren atención inmediata (dolor de pecho, dificultad para respirar, hemorragia, desmayo, fiebre muy alta, dolor insoportable)
  - 🟡 MEDIUM: síntomas que requieren atención médica pero no son emergencia
  - 🟢 LOW: síntomas leves, control o consulta rutinaria

DEVUELVE SOLAMENTE UN JSON VALIDO CON ESTOS 3 CAMPOS:
- specialty: nombre exacto de la especialidad
- urgency: SOLAMENTE: low, medium, high
- reasoning: explicación precisa y clínica de por qué le corresponde esa especialidad y urgencia
        """

        user_prompt = f'Analiza el malestar del paciente y devuelve JSON.\n\nPaciente: "{description}"'

        resp = client.chat.completions.create(
            model=settings.roq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=250,
            response_format={ "type": "json_object" }
        )
        
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        parsed = TriageSchema.model_validate(data)
        u = _normalize_urgency(parsed.urgency)
        return {"specialty": parsed.specialty.strip(), "urgency": u, "reasoning": parsed.reasoning.strip()}
    except Exception as e:
        logger.warning("Roq AI triage failed: %s", e)
        return None


def perform_triage(description: str) -> Dict[str, Any]:
    use_openai = settings.ai_provider in ("openai", "auto") and bool(settings.openai_api_key)
    use_roq = settings.ai_provider in ("roq", "auto") and bool(settings.roq_api_key)

    if use_openai:
        try:
            return _generate_openai_triage(description)
        except Exception as e:
            logger.warning("OpenAI triage failed: %s", e)

    if use_roq:
        result = _generate_roq_triage(description)
        if result:
            return result

    return _fallback_triage(description)
