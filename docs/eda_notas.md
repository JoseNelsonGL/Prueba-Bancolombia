# Notas de EDA y decisiones de modelamiento (Parte 1)

## Reproducibilidad
Todo lo que describe este documento se puede reproducir en código, no solo
leer como texto:
- `notebooks/01_eda.py` — genera el resumen de variables por tabla, la
  evidencia de fuga por correlación (gráfico "antes vs. después" del t-1),
  el embudo de cómo evoluciona el número de variables a lo largo del
  pipeline, y el análisis de nulos/valores inválidos del panel
  demográfico. Salidas en `notebooks/eda_outputs/`.
- `notebooks/02_model_comparison.py` — entrena y compara 3 familias de
  modelos (regresión logística, random forest, LightGBM) sobre el mismo
  split temporal, con curva ROC y selección justificada; además, sobre el
  modelo ganador, corre un backtesting de estabilidad temporal mes a mes y
  genera importancia de variables + SHAP. Salidas en `notebooks/model_outputs/`.

## Bases disponibles
- `trtest.csv`: 568.251 filas (obligación-mes), ago–dic 2023, 400.807 obligaciones únicas, 267.256 clientes únicos. Target balanceado (52%/48%).
- `master_customer_data.csv`: panel mensual jul–dic 2023, 241.049 clientes únicos (~72k/mes). No llega a enero 2024.
- `probabilidad_oblig_base_hist.csv`: panel mensual ene–dic 2023, 458.114 obligaciones únicas (score actual del banco: prob_propension, prob_alrt_temprana, prob_auto_cura, lote).
- `maestra_cuotas_pagos_mes_hist.csv`: panel mensual ene–dic 2023, 458.182 obligaciones únicas (histórico de cuotas/pagos). Nota: `fecha_corte` viene en formato YYYYMMDD (no YYYYMM como las demás tablas); `porc_pago` trae valores `inf` por división entre cuota=0, se limpiaron y se capó a 1000%.
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
subconjunto de variables presente en ambos mundos (76 variables): rezagos
propios de trtest, panel demográfico (as-of, sin mirar al futuro) y scores
del sistema actual de priorización.

**Evidencia empírica (no solo argumento teórico):** `notebooks/01_eda.py`
mide la correlación de estas columnas con el target en su versión
contemporánea vs. su versión rezagada a t-1. La caída es drástica —
`marca_alternativa` pasa de |corr|=0.87 (prácticamente el mismo dato que el
target, porque literalmente describe si aceptó o no la alternativa ESE
mes) a |corr|=0.07 en t-1; `marca_pago` de 0.48 a 0.05; `dias_mora_fin` de
0.35 a 0.00. Ver `notebooks/eda_outputs/01_correlacion_fuga.png`. Esto
confirma que la correlación alta contemporánea es un artefacto de fuga, no
señal predictiva real.

**Cómo evoluciona el conjunto de variables** (ejecutando el pipeline real
paso a paso, ver `notebooks/eda_outputs/02_embudo_variables.png`):
trtest crudo (49 cols) → tras excluir IDs y columnas con fuga (14) → +
historial propio rezagado (45) → + demografía (81) → + scores del banco
(85) → + historial de cuotas/pagos (92) → features finales ∩ con oot.csv
(**76**).

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

## Validación: no se entregaron bases de train/test separadas
`trtest.csv` trae ago-dic 2023 en una sola tabla (no viene partido en train
y test). La partición se hace por CORTE TEMPORAL, no aleatoria: train =
ago–nov 2023 (467.785 filas), validación = dic 2023 (100.466 filas) — el
último mes disponible se deja fuera del entrenamiento, exactamente como
después hay que predecir enero-2024 (`oot.csv`) sin haberlo visto. Se
prefirió esto sobre un split aleatorio 70/30 porque el objetivo real es
pronosticar hacia adelante en el tiempo: un split aleatorio mezclaría
información de diciembre en el entrenamiento y daría una métrica de
validación optimista, que no representa el desempeño real en producción.

Resultado con las 3 tablas iniciales (sin cuotas/pagos): AUC = 0.696, F1
(umbral óptimo 0.325) = 0.660, precisión = 0.53, recall = 0.88.

**Resultado final, con las 4 tablas integradas** (LightGBM, 76 variables
comunes entre trtest y oot): **AUC = 0.729, F1 = 0.671** (umbral óptimo
0.325), precisión = 0.55, recall = 0.86. El historial de pagos
(`maestra_cuotas_pagos_mes_hist`) fue la incorporación de mayor impacto:
`marca_pago_prev` (si pagó más/menos/igual/nada el mes anterior),
`cuota_prev` y `porc_pago_mean_3m` (promedio de cumplimiento en los últimos
3 meses) quedan entre las variables más importantes, junto con los scores
del sistema actual del banco (`prob_propension_prev`,
`prob_alrt_temprana_prev`, `prob_auto_cura_prev`) y la aceptación en el mes
anterior (`prev_var_rpta_alt`).

El modelo final se reentrena con la totalidad de trtest (ago–dic 2023) y se
usa para calificar `oot.csv` (enero 2024), generando `resultado_prueba.csv`
con el mismo orden de filas que `sample_submission.csv`.

## Selección de modelo: por qué LightGBM y no otra alternativa
`notebooks/02_model_comparison.py` entrena, sobre el mismo split temporal y
el mismo conjunto de 76 features, tres familias de algoritmos —lineal,
bagging y boosting— para no elegir LightGBM "por default":

| Modelo | AUC train | AUC valid | Brecha train-valid | F1 valid |
|---|---|---|---|---|
| Regresión Logística | 0.708 | 0.685 | 0.022 | 0.649 |
| Random Forest | 0.730 | 0.705 | 0.025 | 0.660 |
| **LightGBM** | 0.782 | **0.729** | 0.053 | **0.671** |

Criterio de selección: se prioriza el mayor AUC de validación; la brecha
train-valid se usa como desempate solo si dos modelos quedan a menos de
0.005 de AUC (no es el caso aquí: LightGBM saca 2.4 puntos de AUC sobre
Random Forest, una diferencia clara, no ruido). LightGBM gana con margen en
AUC y en F1 (la métrica real de evaluación de la prueba), pese a tener la
brecha train-valid más alta de los tres — un nivel moderado y esperable en
un modelo de boosting, ya activamente controlado en el pipeline
(`feature_fraction`/`bagging_fraction`=0.8, `min_data_in_leaf`=100, early
stopping). Nota metodológica: la comparación favorece estructuralmente a
LightGBM en un aspecto real y no accidental — maneja categóricas/nulos de
forma nativa, mientras que los otros dos necesitaron one-hot + imputación
(con `ciiu`, 446 categorías, agrupado a las 15 más frecuentes por
necesidad); esa capacidad nativa es justamente relevante para estos datos,
no un artefacto que deba corregirse. Ver curva ROC en
`notebooks/model_outputs/roc_comparacion.png`.

## Selección final: estabilidad temporal e interpretabilidad
Con LightGBM ya seleccionado, `notebooks/02_model_comparison.py` corre dos
análisis adicionales sobre ese modelo (no un script aparte, para no
duplicar lógica de entrenamiento):

**Estabilidad temporal** (`estabilidad_temporal.png`/`.csv`): en vez de
confiar en un único mes de validación, se hace backtesting de *ventana
expansiva* — para cada mes desde septiembre, se entrena solo con los meses
anteriores y se mide AUC/F1 en un mes que el modelo nunca vio en ese
entrenamiento. Resultado: **AUC entre 0.714 y 0.754 en los 4 meses
evaluados (media 0.731, desv. estándar 0.017)** — el modelo es estable en
el tiempo, sin señales de degradación abrupta mes a mes. Esto es evidencia
directa a favor de la propuesta de monitoreo de deriva de desempeño en
`docs/mlops_parte1.md` (da un rango de referencia contra el cual comparar
el AUC/F1 real una vez en producción).

**Interpretabilidad** (`feature_importance.png` + `shap_summary.png`): el
ranking de importancia por ganancia confirma lo ya reportado —
`marca_pago_prev`, los 3 scores del banco (`prob_propension_prev`,
`prob_alrt_temprana_prev`, `prob_auto_cura_prev`), `cuota_prev` y
`porc_pago_mean_3m` dominan. El gráfico SHAP añade la DIRECCIÓN del efecto
por observación (no solo qué tan importante es una variable, sino si
empuja la probabilidad hacia arriba o hacia abajo): por ejemplo, mayor
`prev_dias_mora_fin` (más mora el mes anterior) empuja la probabilidad de
aceptación hacia arriba, consistente con que un cliente con más mora
reciente esté más dispuesto a aceptar una opción de pago.
