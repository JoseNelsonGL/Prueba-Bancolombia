# Prueba Técnica — Modelo de Propensión a Aceptación de Opciones de Pago + Sistema Agéntico

Repositorio de la solución end-to-end para la prueba técnica de Bancolombia (gestión de cartera en mora).

## Estructura
- `data/` — datos crudos y procesados (no versionados por tamaño/sensibilidad; ver `.gitignore`)
- `notebooks/` — EDA reproducible y comparación de modelos (Parte 1), con sus salidas (gráficos/tablas) en `notebooks/eda_outputs/` y `notebooks/model_outputs/`
- `src/` — pipeline de datos, entrenamiento, inferencia (Parte 1)
- `agentic/` — prototipo del sistema multiagente (Parte 2)
- `docs/` — documento técnico y diagramas de arquitectura
- `results/` — `resultado_prueba.csv` y artefactos de evaluación
- `tests/` — pruebas funcionales, de integración, seguridad y robustez del sistema agéntico

## Cómo reproducir

```bash
pip install -r requirements.txt

# Coloca las 4 tablas + oot.csv + sample_submission.csv en data/raw/
# (ver docs/eda_notas.md para nombres y formato esperado)

python3 src/data_prep.py   # construye data/processed/modeling_{trtest,oot}.parquet
python3 src/train.py       # entrena, valida y genera results/resultado_prueba.csv

python3 notebooks/01_eda.py             # EDA reproducible: variables por tabla, evidencia de fuga por correlación, embudo de variables, calidad de datos
python3 notebooks/02_model_comparison.py  # compara Regresión Logística / Random Forest / LightGBM y justifica la selección

python3 agentic/main.py    # corre los 13 escenarios simulados del sistema agéntico
python3 -m pytest tests/ -v   # 26 pruebas: reglas de negocio, NBA, guardrails, integración
```

## Documentos (Parte 1 y 2)

- `docs/documento_tecnico.md` — documento técnico principal (≤4.000 caracteres), incluye declaración de uso de IA.
- `docs/eda_notas.md` — EDA, hallazgo de fuga de información (con evidencia de correlación), comparación de modelos y decisiones de features.
- `docs/Documento_Metodologico_Prueba_Bancolombia.docx` — versión formal en Word del documento técnico + anexos detallados.
- `docs/mlops_parte1.md` — cómo el modelo cumple cada criterio de MLOps.
- `docs/arquitectura_agentica.md` — agentes, responsabilidades, orquestación, integración con la Parte 1.
- `docs/pruebas_agentico.md` — escenarios, métricas, umbrales de aceptación y resultados de las pruebas.
- `docs/arquitectura_produccion.md` — propuesta de arquitectura de operación en producción (no implementada).
- `docs/presentacion_ejecutiva.md` — guion de la presentación de 15 min, incluyendo el bloque de 5 min para comité no técnico.

## Estado
Solución completa (Parte 1 + Parte 2) construida con las 4 tablas de datos. Ver commits para el detalle de avance.
