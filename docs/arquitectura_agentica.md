# Arquitectura del sistema agéntico (Parte 2)

## 1. Filosofía de diseño

Cobranza es un dominio regulado: cada oferta que se le hace a un cliente
tiene que ser exactamente la que la política de crédito autoriza, tiene que
quedar trazada, y tiene que poder explicarse ante un regulador o un cliente
que reclama. Por eso la arquitectura separa deliberadamente **qué se puede
ofrecer** (determinístico, basado en reglas, nunca delegado a un modelo de
lenguaje) de **cómo se comunica** (lenguaje natural, donde sí tiene sentido
usar un LLM). Un LLM puede alucinar una condición que no existe; el motor de
reglas de negocio no puede, porque no "redacta", solo evalúa lógica.

Consecuencia de diseño: se eligió un patrón **supervisor lineal y auditable**
(Contexto → Elegibilidad/Reglas → Siguiente Mejor Acción → Conversacional →
Guardrails → Escalamiento) en lugar de un grafo de agentes que se llaman
libremente entre sí (tipo AutoGen/CrewAI "open dialogue"). Para este dominio,
la previsibilidad pesa más que la flexibilidad: cada sesión sigue el mismo
camino y cada decisión es reproducible.

## 2. Agentes y responsabilidades

| Agente | Responsabilidad | Entrada | Salida |
|---|---|---|---|
| **Contexto** | Ensambla el estado de la obligación: datos del cliente, mora, alternativas preaprobadas, historial de aplicaciones/gestiones, scores del modelo de propensión (Parte 1) y de los scores actuales del banco. | Fuentes de datos (core, motor de preaprobación, CRM cobranza, API del modelo Parte 1) | `ClienteObligacion` |
| **Elegibilidad (reglas de negocio)** | Única fuente de verdad de QUÉ se puede ofrecer: aplica máximo 3 opciones/mes, cooldown de 3–4 meses por tipo de alternativa, bloqueo total si ya aceptó una opción vigente, restricciones duras (jurídico/fraude). | `ClienteObligacion` | `DecisionElegibilidad` |
| **Siguiente Mejor Acción (NBA)** | Decide la acción concreta combinando elegibilidad + score de propensión (Parte 1) + señales del banco (auto-cura, alerta temprana): ofrecer opción de pago (y cuál, si hay varias), ofrecer acuerdo de 5 días, diferir por auto-cura, monitorear sin ofrecer, o escalar. | `ClienteObligacion` + `DecisionElegibilidad` | `DecisionNBA` |
| **Conversacional** | Redacta el mensaje y conduce el diálogo (proactivo o reactivo) dentro de lo que el NBA autorizó; interpreta intención del cliente (acepta, rechaza, pide otra alternativa, consulta saldo, dificultad financiera, admite incumplimiento). | `DecisionNBA` + mensaje del cliente | Turno de conversación |
| **Guardrails** | Defensa en profundidad: detecta manipulación/prompt injection, señales sensibles (riesgo personal, amenazas), información contradictoria; valida que la respuesta generada nunca mencione una alternativa no autorizada. | Texto del cliente / texto del agente | Bandera de escalamiento / bloqueo |
| **Escalamiento** | Punto único de handoff a gestor humano, con el contexto completo y el motivo, para que el humano no tenga que reconstruir la conversación. | Señal de cualquier agente anterior | Caso creado en cola humana |
| **Trazabilidad** | Registra cada decisión de cada agente (evento estructurado JSON) con un `session_id` común: auditoría y explicabilidad end-to-end. | Eventos de todos los agentes | Log estructurado |

## 3. Orquestación

El **Orquestador** ejecuta la secuencia Contexto→Reglas→NBA una sola vez por
sesión (la decisión de qué es elegible no cambia dentro de la misma
conversación, salvo que el cliente pida otra alternativa, en cuyo caso el
Conversacional actualiza cuál queda "sobre la mesa", siempre dentro del
conjunto ya autorizado — nunca agrega una nueva). Luego procesa turno a turno
los mensajes del cliente, pasando cada uno primero por Guardrails; si
Guardrails marca escalamiento, el flujo se detiene inmediatamente y no se
genera ninguna respuesta adicional del LLM/plantilla.

Modo **proactivo** (campaña de gestión): el sistema abre la conversación si
el NBA autorizó una oferta. Modo **reactivo** (cliente contacta primero): no
hay apertura; se responde directamente a la intención del cliente, evaluando
igualmente elegibilidad antes de mencionar cualquier alternativa.

## 4. Integración con el modelo analítico (Parte 1)

El score de propensión de la Parte 1 entra al Agente de Contexto como un
campo más (`prob_aceptacion_opcion_pago`), obtenido de un endpoint de
inferencia batch/online (ver `docs/mlops_parte1.md`). El NBA lo usa para:
(a) decidir si vale la pena contactar proactivamente (umbral configurable),
(b) como insumo del ranking cuando hay varias alternativas elegibles, y
(c) junto con `prob_auto_cura`, para diferir gestión intensa en mora muy
temprana con alta probabilidad de autocorrección — evitando fricción y
costo de gestión innecesarios. El sistema es robusto a que este score no
esté disponible (falla del servicio): las reglas de negocio siguen
operando de forma determinística (ver prueba de robustez en
`docs/pruebas_agentico.md`).

## 5. Seguridad, trazabilidad y escalamiento — resumen de mecanismos

- **Seguridad de datos**: todos los identificadores ya llegan enmascarados;
  el prototipo nunca usa nombres reales (perfiles 100% ficticios).
- **Seguridad de decisión**: `guardrails.validar_respuesta_agente` es una
  barrera de salida que bloquea cualquier mensaje que mencione una
  alternativa no autorizada, independientemente de qué generó el texto.
- **Trazabilidad**: cada sesión tiene un `session_id`; cada decisión de cada
  agente queda en `results/trazas_agentico.jsonl` con timestamp y motivo.
- **Explicabilidad**: `DecisionNBA.explicacion` es un texto humano-legible
  de por qué se tomó la acción, generado en el momento de la decisión (no
  post-hoc).
- **Escalamiento a humano**: restricciones duras, señales sensibles,
  intentos de manipulación, información contradictoria, e incumplimiento
  admitido de un acuerdo previo, escalan siempre — ver casos en
  `agentic/mock_data.py` y pruebas en `tests/test_agentic.py`.

## 6. Por qué NO se usó un LLM real en este prototipo

Esta sesión no tuvo acceso a una API de LLM. El prototipo implementa cada
punto de "razonamiento en lenguaje natural" (interpretar intención,
redactar mensajes) con reglas léxicas y plantillas, pero **diseñado con el
punto de extensión explícito** (`GeneradorPlantillas` en
`agentic/conversacional.py`, clase reemplazable por un `GeneradorLLM`) para
que en producción esa pieza se reemplace por un LLM sin tocar el motor de
reglas de negocio ni el NBA. Esto se declara explícitamente como limitación
del entorno de desarrollo, no de la arquitectura propuesta.
