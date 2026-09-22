# Guion de presentación (15 minutos)

Nota: el material de diapositivas no es obligatorio entregarlo junto con la
prueba; este documento es el guion/contenido para prepararlo y para la
sustentación, incluyendo el bloque de 5 minutos pedido explícitamente para
un comité directivo no técnico que debe aprobar el uso del modelo.

## Bloque técnico (≈10 min)

**1. Contexto y objetivo (1.5 min)**
Cartera en mora, opciones de pago y acuerdos como palancas de gestión;
objetivo: anticipar un mes antes la probabilidad de aceptación para
priorizar mejor la gestión, y automatizar el ofrecimiento respetando reglas
de negocio.

**2. Parte 1 — Metodología y decisión clave sobre variables (3 min)**
- 4 tablas, ~570K obligaciones-mes, target balanceado.
- La mayoría de columnas de trtest no están en oot y muestran correlación
  contemporánea muy alta con el target (describen el resultado del mismo
  mes) → se rediseñó el pipeline a variables estrictamente "conocidas
  antes" del mes a predecir.
- Validación temporal (no aleatoria), umbral optimizado a F1.
- Resultado: **AUC 0.729, F1 0.671**, integrando historial de pagos,
  demografía y scores actuales del banco.
- Principal limitación: `oot.csv` no trae elegibilidad/producto vigente →
  la mitad de las obligaciones de enero-2024 son "cold start".

**3. Parte 2 — Sistema agéntico (4 min)**
- Arquitectura supervisor lineal y auditable: Reglas de negocio
  (determinísticas) → Siguiente Mejor Acción (usa el score de la Parte 1)
  → Conversacional → Guardrails → Escalamiento.
- Por qué reglas de negocio SEPARADAS del LLM: en cobranza, la oferta debe
  ser exactamente la autorizada — nunca delegable a que un modelo de
  lenguaje la "invente".
- 14 escenarios dirigidos (los 7 pedidos + robustez + restricción legal),
  49 pruebas automatizadas (42 dirigidas + 7 masivas sobre 400 casos
  sintéticos), tolerancia cero a ofertas no autorizadas.
- Limitación del entorno: sin acceso a LLM real en esta prueba; el
  prototipo usa reglas/plantillas con un punto de extensión explícito para
  conectar un LLM en producción sin tocar el motor de decisión.

**4. Arquitectura de producción y próximos pasos (1.5 min)**
Ciclo completo: feature store → entrenamiento/registro (MLflow) →
scoring batch y on-demand → orquestador agéntico → escalamiento humano →
monitoreo (deriva de datos/desempeño, tasa de ofertas no autorizadas).
Roadmap: reemplazar NLU por reglas con LLM + evaluación continua; validar
PSI de estabilidad poblacional; conseguir el dato de elegibilidad vigente
para el scoring.

## Bloque ejecutivo — comité no técnico (5 min)

Objetivo de este bloque: lograr la aprobación de negocio, no explicar
técnica. Se evita jerga (F1, AUC, LightGBM, LLM) y se traduce todo a
impacto y riesgo.

1. **El problema en una frase (30 s):** "Hoy priorizamos gestión de cartera
   por exposición; con este modelo sabemos, con un mes de anticipación,
   qué clientes son más propensos a aceptar una opción de pago, para
   gestionarlos primero y de forma más personalizada."

2. **El resultado, en términos de negocio (1.5 min):** de cada 10 clientes
   que el modelo marca como "alta probabilidad de aceptar", cerca de 6
   efectivamente aceptan (equivalente de negocio al F1/precisión) — una
   mejora medible frente a priorizar solo por monto de deuda. Se explica
   con un ejemplo numérico simple, no con la fórmula.

3. **Qué automatiza el asistente y qué NO decide solo (1.5 min):** el
   sistema conversacional solo puede ofrecer lo que la política de crédito
   ya autorizó — nunca "inventa" un descuento ni una condición. Cualquier
   caso sensible, dudoso, o fuera de lo normal se transfiere automáticamente
   a un gestor humano. Se muestra un ejemplo de escalamiento real (pantalla
   o transcripción) para dar confianza.

4. **Riesgos y cómo se controlan (1 min):** riesgo de que el modelo se
   "desactualice" → monitoreo mensual con alerta automática; riesgo de que
   el asistente ofrezca algo indebido → bloqueo automático más auditoría
   del 100% de las conversaciones; riesgo reputacional/legal → siempre hay
   un humano disponible y trazabilidad completa de cada decisión.

5. **Pedido concreto de aprobación (30 s):** aprobar un piloto controlado
   (p. ej., un segmento/mes) con monitoreo diario antes de escalar a toda
   la cartera, y definir en conjunto con Riesgo/Jurídico/Cumplimiento el
   umbral de qué se considera un caso "sensible".
