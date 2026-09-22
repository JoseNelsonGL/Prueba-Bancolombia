# Pruebas del sistema agéntico: escenarios, métricas y umbrales

## 0. Por qué se prueba así (y no como el modelo de la Parte 1)

El modelo de propensión (Parte 1) es un sistema **predictivo**: siempre va a
equivocarse en algún porcentaje de los casos, así que se evalúa con métricas
de error (AUC, F1) y se acepta una tasa de falla. El sistema agéntico, en
cambio, codifica **políticas que el banco ya decidió** (máximo 3 opciones/mes,
cooldowns, restricciones duras, escalamiento obligatorio): no está prediciendo
nada, así que el criterio de aceptación correcto no es "una tasa de error
razonable" sino **cero incidentes de cumplimiento** — nunca ofrecer algo no
autorizado, nunca omitir un escalamiento obligatorio. Por eso las pruebas de
reglas de negocio y de seguridad de este documento se exigen al 100%, y por
eso vale la pena invertir en varias capas de prueba, no solo una: como se
documenta en la sección 3, dos capas que pasan sus pruebas por separado
pueden seguir teniendo un hueco cuando se combinan, y solo una prueba de
integración de punta a punta lo revela.

## 1. Pruebas automatizadas (`tests/test_agentic.py`, pytest)

**42 pruebas, 100% pasan.** Se organizan en 6 capas:

| Capa | # pruebas | Qué garantizan |
|---|---|---|
| Funcionales — reglas de negocio | 8 | Máximo 3 opciones/mes, cooldown 3-4 meses respetado y liberado a tiempo, bloqueo total si ya hay opción vigente, restricción dura siempre escala y nunca ofrece, acuerdo de pago solo en mora temprana, **incumplimiento reciente (≤90 días) bloquea y escala automáticamente**, y ese bloqueo se libera pasada la ventana. |
| Funcionales — NBA | 5 | Priorización correcta según mora (alta→alternativas profundas, baja→leves), diferimiento por auto-cura, robustez ante caída del servicio de scoring (scores en `None` no lanza excepción), y la rama de "ofrecer acuerdo de pago" cuando no hay opciones preaprobadas elegibles. |
| Seguridad — guardrails | 9 | Detección de manipulación/prompt injection, señales sensibles (riesgo personal, amenazas), información contradictoria, cero falsos positivos en mensaje neutro, bloqueo de alternativas no autorizadas en la respuesta final, **y bloqueo de identificadores/códigos internos filtrados por error a un mensaje** (bug real corregido, ver sección 3). |
| Funcionales — NLU por reglas (clasificación de intención aislada) | 5 | Que cada patrón léxico clasifique el mensaje en la intención correcta (acepta, rechaza, pide otra alternativa, consulta saldo, dificultad financiera). |
| Funcionales — agente conversacional (respuesta end-to-end, no solo la etiqueta) | 8 | Que la RESPUESTA generada para cada intención sea la correcta, no solo la clasificación: cifras de saldo correctas, no se inventa una alternativa cuando no queda ninguna disponible, mensaje de aclaración ante algo ambiguo, y la interacción entre guardrails y NLU cuando ambos podrían aplicar (ver sección 3). |
| Integración — orquestador end-to-end | 7 | Cliente no elegible nunca recibe transcript con oferta, restricción jurídica escala sin generar ningún mensaje, manipulación detiene el flujo inmediatamente, regresión de "cambio de alternativa" (queda registrada la última, no la original), **incumplimiento detectado proactivamente desde el historial escala sin ningún contacto**, **incumplimiento admitido solo por el cliente escala igual (red de seguridad)**, y los mensajes de apertura de las dos rutas de oferta (acuerdo de pago / diferir por auto-cura) son los correctos. |

**Umbral de aceptación aplicado:** 100% de estas pruebas deben pasar antes de
cualquier despliegue — no se acepta ningún caso donde se ofrezca una
alternativa no autorizada o se omita un escalamiento obligatorio (tolerancia
cero en las pruebas de seguridad y de reglas de negocio, a diferencia de un
modelo estadístico donde se acepta una tasa de error).

## 2. Cobertura de código (`pytest --cov=agentic`)

| Módulo | Cobertura | Qué es |
|---|---|---|
| `models.py`, `orquestador.py`, `nba.py`, `reglas_negocio.py`, `guardrails.py`, `trazabilidad.py` | **100%** | Toda la lógica de decisión, elegibilidad, priorización, seguridad y auditoría. |
| `conversacional.py` | **99%** | Solo queda sin cubrir una línea de respaldo (`return None` final), inalcanzable mientras `TipoAccion` tenga las 5 variantes actuales que ya se manejan explícitamente antes — código defensivo por si se agrega una sexta acción en el futuro, no un hueco de prueba. |
| `main.py`, `mock_data.py` | 0% (excluidos del cálculo relevante) | Guion de demostración y datos ficticios de los 14 escenarios, no lógica de decisión — se validan corriéndolos directamente (ver sección 4), no con pytest. |
| **Total (excluyendo demo/fixtures)** | **≈100% sobre los 6 módulos de decisión, 99% incluyendo conversacional.py** | |

Correr: `python -m pytest tests/ --cov=agentic --cov-report=term-missing`.

## 3. Hallazgos de esta revisión (bugs reales encontrados y corregidos)

Ampliar la batería de pruebas — en particular, probar el agente
conversacional de punta a punta y no solo su clasificador de intención
aislado — sacó a la luz tres problemas reales que ninguna prueba anterior
cubría. Se documentan aquí de forma transparente porque son la evidencia más
concreta de que la batería de pruebas agrega valor real, no solo cobertura
nominal:

1. **Bug de correctitud (el más serio): "no me sirve" se clasificaba como
   ACEPTA.** El patrón léxico de aceptación incluía la frase "me sirve", y
   como se evaluaba antes que el de rechazo, cualquier mensaje que contuviera
   "no me sirve" (un rechazo) se detectaba como una aceptación — el agente
   habría registrado que el cliente aceptó una alternativa que en realidad
   rechazó. Corregido en `conversacional.py` con un lookbehind negativo
   (`(?<!no )\bme sirve\b`); ver `test_rechazo_no_escala_y_deja_oferta_disponible`.
2. **Chequeo de seguridad sin efecto.** `guardrails.validar_respuesta_agente`
   tenía un bucle que recorría los tokens en mayúsculas del mensaje del
   agente pero nunca usaba el resultado — no bloqueaba nada. Corregido para
   que si un mensaje filtra por error un identificador/código interno, se
   bloquee su envío; ver `test_validar_respuesta_bloquea_token_interno_filtrado`.
3. **Regla de negocio incompleta: el incumplimiento reciente solo se
   detectaba si el cliente lo admitía.** Existía una función
   (`hubo_incumplimiento_reciente`) que nunca se usaba en ninguna parte del
   código: el sistema solo escalaba por incumplimiento previo si el cliente
   lo mencionaba en la conversación, aunque el propio historial de gestión ya
   lo tuviera registrado. Se conectó como una regla de negocio de primera
   línea (proactiva, sobre el dato estructurado), dejando la detección
   conversacional como red de seguridad para cuando el dato aún no se ha
   actualizado (rezago) — ver escenarios 4c/4d en la sección 4 y las pruebas
   `test_incumplimiento_reciente_bloquea_y_escala` y
   `test_incumplimiento_admitido_solo_por_cliente_escala_como_red_de_seguridad`.

Ninguno de los tres se veía en las pruebas anteriores porque cada capa se
probaba por separado y en aislamiento; los tres solo se manifiestan al
probar el sistema de punta a punta, con datos que combinan varias señales a
la vez — es la razón por la que la sección 1 ahora incluye una capa completa
de pruebas del agente conversacional además de las de clasificación de
intención aislada.

## 4. Trazabilidad: requisito del enunciado → prueba que lo verifica

| Requisito del enunciado | Prueba(s) |
|---|---|
| Ofrecer únicamente acuerdos/opciones para los que el cliente es elegible | `test_maximo_3_opciones_preaprobadas`, `test_cooldown_bloquea_alternativa_reciente`, `test_opcion_vigente_bloquea_todo_ofrecimiento_nuevo`, `test_cliente_no_elegible_nunca_recibe_oferta` |
| Cooldown de 3-4 meses entre aplicaciones de una misma alternativa | `test_cooldown_bloquea_alternativa_reciente`, `test_cooldown_vencido_habilita_alternativa` |
| Restricciones duras (jurídico/fraude) nunca ofrecen y siempre escalan | `test_restriccion_dura_siempre_escala_y_nunca_ofrece`, `test_restriccion_juridica_escala_sin_ofrecer` |
| Detección de manipulación / prompt injection | `test_detecta_intentos_de_manipulacion`, `test_manipulacion_detiene_flujo_conversacional` |
| Detección de señales sensibles (riesgo personal, amenazas) | `test_detecta_senales_sensibles`, `test_perdida_de_empleo_escala_por_guardrail_antes_del_nlu` |
| Información contradictoria se escala para verificación humana | `test_detecta_informacion_contradictoria` |
| Ninguna respuesta menciona una alternativa no autorizada | `test_validar_respuesta_bloquea_alternativa_no_autorizada`, `test_validar_respuesta_bloquea_token_interno_filtrado` |
| El sistema sigue operando si el modelo de propensión (Parte 1) no responde | `test_robustez_scores_none_no_lanza_excepcion`, escenario `servicio_scoring_no_disponible` |
| Trazabilidad/explicabilidad de cada decisión | `test_resumen_devuelve_los_eventos_registrados_en_la_sesion`, campo `DecisionNBA.explicacion` en todas las pruebas de NBA |
| Cero falsos positivos de escalamiento en mensajes neutros | `test_mensaje_neutro_no_dispara_falsos_positivos` |

## 5. Escenarios funcionales simulados (`agentic/mock_data.py` + `agentic/main.py`)

**14 escenarios** end-to-end (perfiles y conversaciones 100% ficticios),
cubriendo explícitamente los 7 casos pedidos en el enunciado más 3
adicionales de robustez/seguridad:

1. Mora temprana + alta probabilidad de pago → acuerdo de pago a 5 días. ✅
2. Elegible para varias opciones → prioriza y explica una. ✅
3. No elegible / cooldown activo → sin ofertas (`monitoreo_sin_oferta`). ✅
4. Rechaza la propuesta / pide otra alternativa / incumple acuerdo previo → 4 sub-casos:
   - 4a: rechaza. ✅
   - 4b: pide otra alternativa. ✅
   - 4c: el **historial de gestión** ya registra el incumplimiento → escala de forma **proactiva**, sin ningún contacto. ✅
   - 4d (extra, red de seguridad): el historial **todavía no** refleja el incumplimiento, pero el cliente lo admite en la conversación → escala igual por la vía conversacional. ✅
5. Contacto reactivo: consulta de saldo y dificultad financiera → la segunda escala por señal sensible (pérdida de empleo, no por la intención "dificultad financiera" — ver sección 3). ✅
6. Información contradictoria ("no reconozco esa deuda") → escala para verificación humana. ✅
7. Solicitud sensible e intento de manipulación → ambos escalan. ✅
8. (Extra) Restricción jurídica dura → escala directo, cero contacto. ✅
9. (Extra) Servicio de scoring caído → el sistema sigue operando con reglas de negocio. ✅

Resultado observado: 7 de 14 escenarios (50%) terminan en escalamiento a
humano — **no es representativo de la tasa real de escalamiento en
producción**: los escenarios fueron diseñados deliberadamente para
"estresar" cada gatillo de escalamiento, no como muestra aleatoria de la
población de clientes.

## 6. Métricas propuestas para monitoreo en producción

| Métrica | Definición | Umbral propuesto |
|---|---|---|
| Tasa de ofertas no autorizadas | % de mensajes enviados que mencionan una alternativa fuera de lo autorizado por reglas de negocio | **0%** (bloqueo automático, no solo alerta) |
| Precisión del escalamiento | % de escalamientos que un gestor humano confirma como necesarios (vs. innecesarios) | ≥ 85% |
| Recall de señales sensibles | % de mensajes con riesgo real detectados y escalados (medido con muestreo humano periódico) | ≥ 95% (falso negativo es el error costoso aquí) |
| Tiempo a escalamiento | Latencia entre la señal y la creación del caso humano | < 5 s |
| Cobertura de intención | % de mensajes NO clasificados como "ambiguo" | ≥ 80% (umbral para decidir si conviene reemplazar reglas por LLM en producción) |
| Tasa de aceptación por acción NBA | % de ofertas aceptadas, por tipo de acción | Línea base a establecer en piloto; se compara contra el `prob_aceptacion_opcion_pago` del modelo Parte 1 para medir calibración |
| Concordancia guardrail ↔ NLU | % de mensajes donde guardrails y el clasificador de intención "compiten" por el mismo mensaje (ver sección 3) | Monitoreo, no umbral — señal para revisar si el orden de precedencia sigue siendo el correcto a medida que cambian los patrones de lenguaje reales |

## 7. Resultados y oportunidades de mejora

- El módulo de NLU basado en reglas léxicas cubre bien los patrones
  probados, pero es frágil ante variación real de lenguaje (jerga regional,
  errores de tipeo, mensajes de voz transcritos) y, como muestra la sección
  3, ante el orden de precedencia entre patrones que se solapan.
  **Oportunidad de mejora prioritaria**: reemplazar `_detectar_intencion`
  por un LLM con salida estructurada (function calling), manteniendo el
  guardrail de reglas como red de seguridad — no como reemplazo.
- La priorización de alternativas cuando hay varias elegibles usa un orden
  fijo por severidad de mora (supuesto de negocio, ver
  `docs/arquitectura_agentica.md`); en producción debería aprenderse de
  datos de aceptación histórica por tipo de alternativa y segmento.
- Falta prueba de carga/concurrencia (fuera de alcance de este prototipo);
  se propone en `docs/arquitectura_produccion.md`.
- Los tres hallazgos de la sección 3 sugieren una práctica a mantener en
  producción: cada vez que se agregue o cambie un patrón léxico (guardrail o
  NLU), correr la suite completa de integración, no solo las pruebas
  unitarias de esa capa — es la única forma en que este tipo de interacción
  entre capas se detecta antes de producción.
