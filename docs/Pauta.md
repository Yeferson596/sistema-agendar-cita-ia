# Checklist de entrega según la pauta

Este documento resume el cumplimiento de la pauta de evaluación para el proyecto MediFlow.

## 1. Cobertura de criterios

- **IE1 - Caso organizacional**: Definido para una clínica médica que necesita triaje, agenda y reducción de inasistencias.
- **IE2 - Selección de IA/LLM/RAG**: Implementado con Gemini y un asistente RAG que usa documentos internos y externos.
- **IE3 - Arquitectura**: Se muestra una solución de frontend React + backend FastAPI + base de datos + servicios de IA/RAG.
- **IE4 - Flujo de información**: El asistente recibe pregunta, recupera contexto y genera respuesta con fuentes referenciadas.
- **IE5 - Justificación técnica**: Documentada en `docs/Informe.md` y reflejada en el diseño de prompts, servicios y decisiones.
- **IE6 - Diagrama de arquitectura**: Incluido en `docs/Informe.md` con Mermaid.
- **IE7 - Diseño y limitaciones**: Se documenta el prompt RAG, la entrega de instrucciones y las limitaciones de prototipo.
- **IE8 - Documentación y pruebas**: Hay documentación técnica y pruebas backend para el endpoint RAG.
- **IE9 - Lenguaje técnico estructurado**: El informe y el README usan lenguaje profesional y enfoque técnico.

## 2. Validación ejecutada

- Backend:
  - `pytest -q` ✅
  - `backend/tests/test_health.py`
  - `backend/tests/test_rag.py`
- Frontend:
  - `npm run lint` ✅
  - `npm run build` ✅

## 3. Componentes clave

- `backend/app/services/rag_assistant.py`
- `backend/app/routers/rag.py`
- `backend/app/data/internal_medical_knowledge.md`
- `backend/app/data/external_medical_guidelines.md`
- `backend/tests/test_rag.py`
- `frontend/src/components/AssistantPanel.tsx`
- `frontend/src/App.tsx`
- `docs/Informe.md`

## 4. Estado actual

- El backend está funcional y validado con pruebas automáticas.
- El frontend compila correctamente y cuenta con un diseño de login moderno.
- El flujo RAG está integrado y documentado.

## 5. Recomendaciones de entrega

- No incluir credenciales reales en el repositorio.
- Mantener `backend/.env` fuera del control de versiones.
- Entregar `README.md`, `docs/Informe.md`, `docs/Pauta.md` y los archivos de prueba.
