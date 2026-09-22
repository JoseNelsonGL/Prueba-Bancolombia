# Prueba Técnica — Modelo de Propensión a Aceptación de Opciones de Pago + Sistema Agéntico

Repositorio de la solución end-to-end para la prueba técnica de Bancolombia (gestión de cartera en mora).

## Estructura
- `config.py` — **único archivo que hay que editar para reproducir con otra ubicación de los datos** (rutas de las 6 tablas de entrada; ver "Cómo reproducir" abajo)
- `data/` — datos crudos y procesados (no versionados por tamaño/sensibilidad; ver `.gitignore`)
- `notebooks/` — EDA reproducible, comparación de modelos y validación de la muestra OOT entregada (Parte 1), con sus salidas (gráficos/tablas) en `notebooks/eda_outputs/`, `notebooks/model_outputs/` y `notebooks/oot_outputs/`
- `src/` — pipeline de datos, entrenamiento, inferencia (Parte 1)
- `agentic/` — prototipo del sistema multiagente (Parte 2)
- `docs/` — documento técnico y diagramas de arquitectura
- `results/` — `resultado_prueba.csv` y artefactos de evaluación
- `tests/` — pruebas funcionales, de integración, seguridad y robustez del sistema agéntico
- `Dockerfile` + `docker/requirements.txt` — imagen de scoring de la Parte 1 (`docker build -t prueba-bancolombia-scoring .`)
- `.github/workflows/ci.yml` — CI real: corre las 42 pruebas y construye la imagen Docker en cada push/PR a `main`

## Cómo reproducir

**Paso 1 — datos:** abre `config.py` (en la raíz del repo) y revisa las 6 rutas de
archivo. Por defecto asumen que las 4 tablas + `oot.csv` + `sample_submission.csv`
están dentro de `data/raw/` con los nombres originales de la prueba (ver
`docs/eda_notas.md` para el detalle de cada tabla) — si tus copias están en otro
lugar o con otro nombre, edita esas líneas ahí y nada más. Ningún otro
archivo del repositorio necesita cambios.

**Paso 2 — instalar y correr:**

```bash
pip install -r requirements.txt

python3 src/data_prep.py   # construye data/processed/modeling_{trtest,oot}.parquet
python3 src/train.py       # entrena, valida y genera results/resultado_prueba.csv

python3 notebooks/01_eda.py                  # EDA reproducible: variables por tabla, evidencia de fuga por correlación, embudo de variables, calidad de datos
python3 notebooks/02_model_comparison.py     # compara Regresión Logística / Random Forest / LightGBM, selección final, estabilidad temporal y SHAP
python3 notebooks/03_analisis_oot_puntuada.py  # valida la muestra OOT entregada (resultado_prueba.csv): sanity checks, PSI y SHAP

python3 agentic/main.py    # corre los 14 escenarios simulados del sistema agéntico
python3 -m pytest tests/ -v   # 42 pruebas: reglas de negocio, NBA, guardrails, integración
python3 -m pytest tests/ --cov=agentic --cov-report=term-missing  # cobertura (ver docs/pruebas_agentico.md)
```

## Documentos (Parte 1 y 2)

- `docs/documento_tecnico.md` — documento técnico principal (≤4.000 caracteres), incluye declaración de uso de IA.
- `docs/eda_notas.md` — EDA, variables excluidas por disponibilidad en oot y consistencia temporal (con evidencia de correlación), comparación de modelos y decisiones de features.
- `docs/Documento_Metodologico_Prueba_Bancolombia.docx` — versión formal en Word del documento técnico + anexos detallados.
- `docs/mlops_parte1.md` — cómo el modelo cumple cada criterio de MLOps.
- `docs/arquitectura_agentica.md` — agentes, responsabilidades, orquestación, integración con la Parte 1.
- `docs/pruebas_agentico.md` — escenarios, métricas, umbrales de aceptación y resultados de las pruebas.
- `docs/arquitectura_produccion.md` — propuesta de arquitectura de operación en producción (no implementada).
- `docs/presentacion_ejecutiva.md` — guion de la presentación de 15 min, incluyendo el bloque de 5 min para comité no técnico.

## Estado
Solución completa (Parte 1 + Parte 2) construida con las 4 tablas de datos. Ver commits para el detalle de avance.
