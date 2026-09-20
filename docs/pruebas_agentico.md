# Pruebas del sistema agéntico: escenarios, métricas y umbrales

## 1. Pruebas automatizadas (`tests/test_agentic.py`, pytest)

26 pruebas, 100% pasan. Se organizan en 4 capas:

| Capa | # pruebas | Qué garantizan |
|---|---|---|
| Funcionales — reglas de negocio | 6 | Máximo 3 opciones/mes, cooldown 3-4 meses respetado y liberado a tiempo, bloqueo total si ya hay opción vigente, restricción dura siempre escala y nunca ofrece, acuerdo de pago solo en mora temprana. |
| Funcionales — NBA | 4 | Priorización correcta según mora (alta→alternativas profundas, baja→leves), diferimiento por auto-cura, **robustez** ante caída del servicio de scoring (scores en `None` no lanza excepción). |
| Seguridad — guardrails | 5 | Detección de manipulación/prompt injection, señales sensibles (riesgo personal, amenazas), información contradictoria, cero falsos positivos en mensaje neutro, bloqueo de alternativas no autorizadas en la respuesta final. |
| Integración — orquestador end-to-end | 4 | Cliente no elegible nunca recibe transcript con oferta, restricción jurídica escala sin generar ningún mensaje, manipulación detiene el flujo inmediatamente, y (prueba de regresión) tras un cambio de alternativa la aceptación registra la ALTERNATIVA CORRECTA, no la original. |

**Umbral de aceptación aplicado:** 100% de estas pruebas deben pasar antes de
cualquier despliegue — no se acepta ningún caso donde se ofrezca una
alternativa no autorizada o se omita un escalamiento obligatorio (tolerancia
cero en las pruebas de seguridad y de reglas de negocio, a diferencia de un
modelo estadístico donde se acepta una tasa de error).

## 2. Escenarios funcionales simulados (`agentic/mock_data.py` + `agentic/main.py`)

13 escenarios end-to-end (perfiles y conversaciones 100% ficticios),
cubriendo explícitamente los 7 casos pedidos en el enunciado más 2
adicionales de robustez/seguridad:

1. Mora temprana + alta probabilidad de pago → acuerdo de pago a 5 días. ✅
2. Elegible para varias opciones → prioriza y explica una. ✅
3. No elegible / cooldown activo → sin ofertas (`monitoreo_sin_oferta`). ✅
4. Rechaza la propuesta / pide otra alternativa / incumple acuerdo previo → 3 sub-casos, el último escala. ✅
5. Contacto reactivo: consulta de saldo y dificultad financiera → la segunda escala por señal sensible. ✅
6. Información contradictoria ("no reconozco esa deuda") → escala para verificación humana. ✅
7. Solicitud sensible e intento de manipulación → ambos escalan. ✅
8. (Extra) Restricción jurídica dura → escala directo, cero contacto. ✅
9. (Extra) Servicio de scoring caído → el sistema sigue operando con reglas de negocio. ✅

Resultado observado: 6 de 13 escenarios (46%) terminan en escalamiento a
humano — **no es representativo de la tasa real de escalamiento en
producción**: los escenarios fueron diseñados deliberadamente para
"estresar" cada gatillo de escalamiento, no como muestra aleatoria de la
población de clientes.

## 3. Métricas propuestas para monitoreo en producción

| Métrica | Definición | Umbral propuesto |
|---|---|---|
| Tasa de ofertas no autorizadas | % de mensajes enviados que mencionan una alternativa fuera de lo autorizado por reglas de negocio | **0%** (bloqueo automático, no solo alerta) |
| Precisión del escalamiento | % de escalamientos que un gestor humano confirma como necesarios (vs. innecesarios) | ≥ 85% |
| Recall de señales sensibles | % de mensajes con riesgo real detectados y escalados (medido con muestreo humano periódico) | ≥ 95% (falso negativo es el error costoso aquí) |
| Tiempo a escalamiento | Latencia entre la señal y la creación del caso humano | < 5 s |
| Cobertura de intención | % de mensajes NO clasificados como "ambiguo" | ≥ 80% (umbral para decidir si conviene reemplazar reglas por LLM en producción) |
| Tasa de aceptación por acción NBA | % de ofertas aceptadas, por tipo de acción | Línea base a establecer en piloto; se compara contra el `prob_aceptacion_opcion_pago` del modelo Parte 1 para medir calibración |

## 4. Resultados y oportunidades de mejora

- El módulo de NLU basado en reglas léxicas cubre bien los patrones
  probados, pero es frágil ante variación real de lenguaje (jerga regional,
  errores de tipeo, mensajes de voz transcritos). **Oportunidad de mejora
  prioritaria**: reemplazar `_detectar_intencion` por un LLM con salida
  estructurada (function calling), manteniendo el guardrail de reglas como
  red de seguridad — no como reemplazo.
- La priorización de alternativas cuando hay varias elegibles usa un orden
  fijo por severidad de mora (supuesto de negocio, ver
  `docs/arquitectura_agentica.md`); en producción debería aprenderse de
  datos de aceptación histórica por tipo de alternativa y segmento.
- Falta prueba de carga/concurrencia (fuera de alcance de este prototipo);
  se propone en `docs/arquitectura_produccion.md`.
