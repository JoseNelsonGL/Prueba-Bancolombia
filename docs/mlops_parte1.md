# MLOps — Modelo de propensión a aceptación de opciones de pago (Parte 1)

Candidato externo: se propone una arquitectura agnóstica de plataforma
(portable a AWS/Azure/GCP o al stack interno del banco), con herramientas
open-source ampliamente adoptadas en la industria.

## 1. Preparación de datos

- **Fuente → feature store**: las 4 tablas (trtest, master_customer_data,
  probabilidad_oblig_hist, maestra_cuotas_pagos_mes_hist) se ingestan vía
  jobs batch (Airflow/Prefect) desde el data lake del banco hacia una capa
  curada (Delta Lake / BigQuery / Redshift).
- **Pipeline de features versionado**: `src/data_prep.py` es la
  implementación de referencia — construye, para cada obligación-mes, un
  corte estrictamente "as-of" (solo información de t-1 hacia atrás),
  evitando el uso de variables no disponibles al momento real de la
  decisión (ver análisis en `docs/eda_notas.md`). En producción este
  código se registra en un
  **feature store** (Feast, o tablas Delta con función de punto-en-el-tiempo)
  para garantizar que entrenamiento e inferencia usan EXACTAMENTE la misma
  lógica de construcción de variables (paridad train/serve).
- **Validación de calidad**: se propone `Great Expectations` (o `pandera`)
  para validar rangos, nulos esperados y esquemas antes de cada
  entrenamiento/scoring, con alertas automáticas si la calidad se degrada.

## 2. Entrenamiento

- **Algoritmo**: LightGBM (maneja categóricas y nulos nativamente, rápido
  sobre ~570K filas, buen desempeño en tabular con desbalance moderado).
- **Validación**: split temporal (nunca aleatorio) — entrena con meses
  anteriores, valida con el último mes disponible, replicando el escenario
  real de "predecir el mes siguiente". Optimización de umbral para F1
  (métrica de la prueba) en vez de 0.5 por defecto.
- **Tracking de experimentos**: MLflow — cada corrida registra
  hiperparámetros, métricas (AUC, F1, precisión, recall), `feature_cols.json`
  y el artefacto del modelo, permitiendo comparar y hacer rollback.
- **Registro de modelos**: MLflow Model Registry con etapas
  `Staging → Production`, y aprobación manual (o automática si supera el
  umbral de F1 del modelo vigente) para promover.

## 3. Inferencia

- **Batch mensual** (caso principal, alineado al ciclo de negocio: "conocer
  con un mes de anticipación"): job programado que corre `src/train.py`
  (modo scoring) sobre la población vigente y publica los scores a la tabla
  que alimenta la priorización por lotes existente.
- **Online/on-demand** (para el sistema agéntico, Parte 2): el mismo modelo
  se sirve detrás de un endpoint (FastAPI + contenedor, o el registry de
  MLflow con `mlflow models serve`), consultado por el Agente de Contexto
  con el `num_oblig_enmascarado` como llave. Se cachea a nivel diario para
  no recalcular en cada interacción.
- **Paridad**: el endpoint de inferencia reutiliza el mismo módulo
  `src/data_prep.py`/`feature_cols.json` que el entrenamiento — de nuevo,
  la razón de tener el pipeline como código versionado y no como notebook.

## 4. Productización

- **Empaquetado como contenedor Docker — implementado, no solo descrito**:
  `Dockerfile` (raíz del repo) + `docker/requirements.txt` (dependencias
  mínimas de scoring, sin las de EDA/notebooks/pruebas) empaquetan
  `src/data_prep.py` + `src/train.py` + `config.py`. Construir:
  `docker build -t prueba-bancolombia-scoring .`. Datos y modelo NO viajan
  en la imagen (se montan como volumen aquí; en producción real vendrían
  del feature store y del MLflow Model Registry al arrancar) — versión
  etiquetada por commit vía el tag de la imagen.
- Contrato de datos explícito (`schema.json` de entrada/salida) para que el
  sistema agéntico y la priorización por lotes tengan una interfaz estable
  — pendiente de implementar (propuesta, ver limitación al final).
- Pruebas de contrato (`pytest`) que corren en CI antes de construir la
  imagen: mismas columnas, mismos tipos, ausencia de las columnas "leaky"
  identificadas en el EDA.

## 5. Despliegue continuo (CI/CD)

- **CI — implementado, no solo descrito**: `.github/workflows/ci.yml`
  corre en cada push/PR a `main`: (a) las 42 pruebas del sistema agéntico
  (`pytest tests/`), y (b) `docker build` de la imagen de scoring, para
  detectar de inmediato si algo rompe el empaquetado.
- **CD** (propuesto, no implementado — requeriría infraestructura de
  despliegue real): al hacer merge a `main` con el tag `model-release`,
  pipeline que (a) reentrena con datos más recientes, (b) compara F1 contra
  el modelo en `Production` en un set de validación común (shadow
  evaluation), y (c) promueve automáticamente solo si mejora o iguala
  dentro de una tolerancia, dejando aprobación manual como opción para
  casos límite.
- Despliegue **canario** (propuesto): el modelo nuevo puntúa en paralelo al
  vigente durante 1-2 semanas antes de reemplazarlo, comparando
  distribución de scores y tasa de aceptación real observada.

## 6. Monitoreo

- **Deriva de datos (data drift)**: PSI / KS por variable clave
  (`prob_propension_prev`, `porc_pago_mean_3m`, mora, demografía) mes a mes,
  con alertas si el PSI supera 0.2 (regla estándar de la industria).
- **Deriva de desempeño**: F1/AUC real vs. predicho, calculable con rezago
  de 1 mes (cuando se observa si el cliente aceptó o no); reentrenamiento
  disparado automáticamente si el F1 cae más de X puntos porcentuales bajo
  el de referencia.
- **Calidad de servicio**: latencia del endpoint, tasa de errores, cobertura
  de features (¿cuántas obligaciones llegan con datos faltantes de las
  tablas panel, como se documentó en el EDA?).
- **Observabilidad**: dashboards (Grafana/Looker) alimentados por los
  registros de MLflow + logs del endpoint; alertas a Slack/PagerDuty del
  equipo de riesgo.

## Riesgos y supuestos (resumen)

- El panel `master_customer_data` no llega a enero-2024 y es disperso →
  se usa el snapshot más reciente disponible (lag real de producción).
- `oot.csv` no trae `producto`/`banca`/`cant_alter_posibles` → el modelo de
  producción real debería tener acceso a la elegibilidad vigente al momento
  del scoring; se recomienda solicitar ese dato adicional (ver documento
  técnico).
- Los cooldowns de opciones de pago (3–4 meses) se documentan como supuesto
  parametrizable, a validar con el área de política de cartera.
- El `docker build` de la imagen de scoring no se pudo probar de punta a
  punta en el entorno donde se preparó este repositorio (política de red
  del entorno bloquea la descarga de la imagen base desde Docker Hub); se
  verificó por otra vía que las dependencias ancladas instalan sin error
  en un entorno limpio, y el propio CI (`.github/workflows/ci.yml`)
  construye la imagen en la infraestructura de GitHub —con acceso normal a
  internet— la primera vez que se suba el repositorio, cerrando esa
  verificación automáticamente.
