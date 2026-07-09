KNOWLEDGE_TOOL_DESCRIPTION = (
    "Busca información médica relevante en la memoria de conocimiento RAG. "
    "Entrada: pregunta del paciente. Salida: texto con fragmentos relevantes y fuentes."
)

TRIAGE_TOOL_DESCRIPTION = (
    "Clasifica síntomas y determina especialidad y urgencia. "
    "Entrada: descripción del cuadro clínico. Salida: JSON con specialty, urgency y reasoning."
)

PREDICT_NO_SHOW_TOOL_DESCRIPTION = (
    "Calcula el riesgo de no-show para una cita. "
    "Entrada: JSON con specialty, urgency y start_at (ISO). "
    "Salida: JSON con no_show_risk, reasoning y features."
)

AGENT_INSTRUCTION = (
    "Actúa como un asistente médico de apoyo, usa las herramientas disponibles para responder "
    "consultas clínicas, predicción de no-show y búsqueda de conocimiento. Prioriza claridad, seguridad "
    "y referencias a documentos cuando las herramientas aporten datos relevantes."
)
