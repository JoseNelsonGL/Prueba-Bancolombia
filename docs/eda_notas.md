# Notas de EDA y decisiones de modelamiento (Parte 1)

## Bases disponibles
- `trtest.csv`: 568.251 filas (obligación-mes), ago–dic 2023, 400.807 obligaciones únicas, 267.256 clientes únicos. Target balanceado (52%/48%).
- `master_customer_data.csv`: panel mensual jul–dic 2023, 241.049 clientes únicos (~72k/mes). No llega a enero 2024.
- `probabilidad_oblig_base_hist.csv`: panel mensual ene–dic 2023, 458.114 obligaciones únicas (score actual del banco: prob_propension, prob_alrt_temprana, prob_auto_cura, lote).
- `maestra_cuotas_pagos_mes_hist.csv`: pendiente de integrar (histórico de cuotas/pagos).
- `oot.csv` / `sample_submission.csv`: 112.549 obligaciones, enero 2024, formato objetivo de entrega. Solo trae ID + fecha (ninguna variable de producto/mora/alternativas).

## Hallazgo crítico: fuga de información (data leakage)
La mayoría de las columnas de `trtest.csv` (gestiones, pagos, promesas, acuerdos,
alternativa aplicada, marca_alternativa, dias_mora_fin, saldo_capital, etc.)
describen **eventos ocurridos durante el mismo mes de la variable respuesta**,
es decir, son consecuencia o coocurrencia directa de la decisión que se
quiere predecir. Usarlas como features contemporáneas sería fuga de
información y el modelo no funcionaría en producción (esas variables no
existen todavía cuando hay que hacer el pronóstico un mes antes).

**Decisión metodológica:** estas columnas solo se usan como fuente de
variables *rezagadas* (estado del mes t-1 de la misma obligación), nunca en
su versión del mes t. Se mantienen como contemporáneas únicamente las que
describen la oferta/elegibilidad vigente (banca, segmento, producto,
cant_alter_posibles, códigos de alternativas preaprobadas) — pero estas
tampoco existen en `oot.csv`, así que el modelo final solo puede usar el
subconjunto de variables presente en ambos mundos (69 variables): rezagos
propios de trtest, panel demográfico (as-of, sin mirar al futuro) y scores
del sistema actual de priorización.

## Limitaciones de cobertura (reales, no error de pipeline)
- ~80% de las obligaciones de `oot.csv` NO tienen historial propio en
  `trtest` (aparecen por primera vez en el programa de gestión) →
  "cold start": sin rezagos de mora/pago propios, el modelo depende de
  demografía + score histórico del banco.
- El panel `master_customer_data` es disperso (promedio 1.78 snapshots por
  cliente en 6 meses): ~20% de los clientes de trtest nunca aparecen en él,
  y aun estando cubiertos, el snapshot más reciente disponible antes del
  corte puede no existir → ~37-50% de nulos en variables demográficas. Se
  deja como missing (LightGBM lo maneja nativamente) más una bandera
  `tiene_snapshot_demografico`.
- `master_customer_data` no llega a enero-2024: el scoring OOT usa el
  snapshot de diciembre-2023 como "as-of" más reciente disponible — lag de
  información real de producción, se documenta como supuesto.

## Validación
Split temporal (no aleatorio): train = ago–nov 2023, validación = dic 2023,
simulando el escenario real (predecir el mes siguiente). Resultado baseline
(LightGBM, sin la tabla de cuotas/pagos todavía):
- AUC = 0.696, F1 (umbral óptimo 0.325) = 0.660, precisión = 0.53, recall = 0.88.

Variables más importantes: score de propensión actual del banco
(`prob_propension_prev`), aceptación en el mes anterior
(`prev_var_rpta_alt`), score de auto-cura y alerta temprana, ubicación
geográfica, tipo de alternativa aplicada el mes anterior, mora previa y
lote de priorización actual.
