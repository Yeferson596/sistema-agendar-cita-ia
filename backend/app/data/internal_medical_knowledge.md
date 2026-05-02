# Conocimiento interno de MediFlow

## Contexto organizacional
MediFlow es una solución para agendar citas médicas con soporte para triaje automático y predicción de no-show.
La organización ofrece atención de especialidades comunes como Medicina General, Odontología, Pediatría, Cardiología y Traumatología.

## Recursos internos
- Historial de citas de pacientes.
- Especialidades médicas con horarios definidos.
- Cálculos de riesgo de inasistencia basados en estadísticas de paciente y especialidad.
- Valoraciones de urgencia asociadas a síntomas.

## Flujo de atención
1. El paciente describe sus síntomas.
2. El sistema realiza un triaje para sugerir especialidad y urgencia.
3. Se consulta disponibilidad de horarios para la especialidad y nivel de urgencia.
4. Se agenda la cita y se calcula riesgo de no-show.

## Objetivos de la solución
- Mejorar la experiencia del paciente al recibir orientación médica rápida.
- Reducir las citas no asistidas mediante alertas de riesgo.
- Usar IA para apoyar el triaje y tomar decisiones más informadas.

## Datos y uso interno
- Las respuestas de triaje se guardan junto con la cita.
- El análisis de no-show utiliza datos estructurados de la base de datos.
- El modelo de triage con Gemini se activa solo cuando existe `GEMINI_API_KEY`.
- En ausencia de la clave, el sistema usa reglas locales para garantizar operación.
