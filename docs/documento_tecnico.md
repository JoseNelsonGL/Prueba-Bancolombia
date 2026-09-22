# Documento Técnico — Prueba Bancolombia (Jose Nelson González)

## Parte 1 — Modelo de propensión

**Proceso:** se recibieron 4 tablas (trtest, master_customer_data, probabilidad_oblig_hist, maestra_cuotas_pagos_mes_hist) y oot.csv (enero-2024, solo IDs). El EDA reveló el hallazgo central: la mayoría de columnas de trtest (gestiones, pagos, alternativa aplicada, mora fin de mes) describen el resultado del mismo mes a predecir → fuga de información si se usan tal cual. Se rediseñó el pipeline para usar solo información de t-1 hacia atrás (lags propios de la obligación, snapshot demográfico más reciente ≤ corte, scores históricos del banco), replicando el escenario real de pronosticar un mes antes.

**Decisiones clave:** LightGBM (categóricas/nulos nativos); validación temporal (train ago-nov 2023, valid dic-2023, no aleatoria); umbral optimizado para F1. Resultado con las 4 tablas integradas: AUC=0.729, F1=0.671 en validación (el historial de pagos fue la incorporación de mayor impacto).

**Supuestos:** snapshot demográfico de dic-2023 usado como "as-of" para enero-2024 (el panel no llega a esa fecha); nulos demográficos (~40-50%) tratados como missing informativo (bandera `tiene_snapshot_demografico`), no imputados.

**Riesgos/limitaciones:** oot.csv no trae producto/banca/elegibilidad vigente, por lo que ~50% de sus obligaciones son "cold start" y dependen solo de demografía + scores del banco; el panel demográfico es disperso; se validó PSI dic-2023 vs. oot=0.013 (sin cambio poblacional relevante); SHAP de oot coincide 8/10 con validación.

**Dato adicional recomendado:** un snapshot de elegibilidad/producto vigente al momento del scoring (ausente hoy en oot.csv) mejoraría el modelo para obligaciones nuevas; costo bajo, pues el motor de preaprobación ya genera esa información mensualmente.

## Parte 2 — Sistema agéntico

**Arquitectura:** patrón supervisor lineal y auditable — Contexto → Reglas de negocio (única fuente de verdad sobre qué ofrecer, determinística) → Siguiente Mejor Acción (integra el score de la Parte 1) → Conversacional → Guardrails → Escalamiento, con trazabilidad JSON por sesión. En un dominio regulado, la previsibilidad de un flujo lineal pesa más que la flexibilidad de un grafo de agentes libre.

**Sin acceso a LLM en este entorno:** intención y redacción se implementaron con reglas léxicas/plantillas, con punto de extensión explícito (`GeneradorPlantillas`) para reemplazar por un LLM real sin tocar el motor de reglas — el LLM redactaría, nunca decidiría qué ofrecer.

**Pruebas:** 26 pruebas automatizadas (reglas de negocio, NBA, guardrails, integración end-to-end) + 13 escenarios simulados cubriendo los 7 casos pedidos más robustez (caída del servicio de scoring) y restricción jurídica dura. Umbral: 0% de ofertas no autorizadas y 0% de restricciones ignoradas (tolerancia cero). Detalle en anexos.

**Riesgos:** el NLU por reglas es frágil ante lenguaje real no anticipado; la priorización entre alternativas usa un orden fijo por severidad de mora (supuesto a validar), no aprendido de datos históricos de aceptación.

**Conclusión general:** ambos componentes son viables como prototipo demostrable dentro del alcance y tiempo de la prueba. El mayor riesgo de negocio no es el desempeño puntual del modelo sino la fuga de información si no se audita qué variables están realmente disponibles al momento de decidir — hallazgo válido tanto para la Parte 1 como para su integración con la Parte 2.

## Declaración de uso de IA generativa

Se usó Claude (Anthropic) como asistente de desarrollo de extremo a extremo: análisis exploratorio, identificación del riesgo de fuga de información, diseño del pipeline de features, entrenamiento del modelo, diseño de la arquitectura agéntica, e implementación de reglas/agentes/pruebas/documentación. El candidato dirigió el alcance, las decisiones de negocio (cooldowns, prioridades, qué construir dado el tiempo disponible) y revisó los resultados y supuestos antes de la entrega.
