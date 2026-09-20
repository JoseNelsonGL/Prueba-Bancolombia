# Arquitectura de producción y operación (propuesta, no implementada)

Visión end-to-end de cómo operarían en conjunto el modelo de propensión
(Parte 1) y el sistema agéntico (Parte 2) en un entorno productivo,
independiente de proveedor cloud.

## 1. Vista de componentes

```
[Core bancario / CRM cobranza / Motor de preaprobación]
              │  (batch nocturno + eventos)
              ▼
     [Data Lake / Lakehouse curado]  ──► [Feature Store]
              │                                │
              ▼                                ▼
   [Pipeline de entrenamiento         [Servicio de inferencia
    (Airflow + MLflow)]                del modelo Parte 1
              │                        (FastAPI + Model Registry)]
              ▼                                │
   [Model Registry: Staging/Prod] ─────────────┘
                                                 │  score de propensión
                                                 ▼
                          [Sistema Agéntico — Orquestador]
                          Contexto → Reglas de negocio → NBA →
                          Conversacional (LLM) → Guardrails
                                │            │            │
                                ▼            ▼            ▼
                         [Canal cliente]  [Cola de     [Observabilidad /
                         WhatsApp/Call    escalamiento  Trazas /
                         center/App       humano]       LLMOps monitor]
```

## 2. Ciclo completo de operación

1. **Ingesta y features** (diaria/mensual según fuente): las 4 familias de
   datos (comportamiento de la obligación, demografía, scores actuales del
   banco, historial de pagos) se actualizan en el feature store con lógica
   de punto-en-el-tiempo idéntica a la de entrenamiento (evita el riesgo de
   fuga documentado en el EDA).
2. **Entrenamiento/reentrenamiento** (mensual o disparado por deriva):
   pipeline reproducible, versionado, con aprobación de promoción vía
   comparación contra el modelo vigente (ver `docs/mlops_parte1.md`).
3. **Scoring batch mensual**: alimenta la priorización por lotes existente
   del banco con la nueva variable de propensión.
4. **Scoring on-demand**: el sistema agéntico consulta el score vigente por
   obligación al iniciar cada sesión de gestión (cacheado a nivel diario).
5. **Gestión agéntica** (proactiva por campaña, o reactiva por contacto
   entrante): el orquestador decide y conversa dentro de los límites de las
   reglas de negocio; cada decisión y cada turno quedan trazados.
6. **Escalamiento humano**: casos con restricciones, señales sensibles,
   manipulación, información contradictoria o incumplimiento quedan en una
   cola con el contexto completo (evita que el gestor humano tenga que
   reconstruir la conversación).
7. **Observabilidad y feedback**: resultado real (¿aceptó?, ¿pagó?) se
   captura y retroalimenta tanto el monitoreo del modelo (Parte 1) como las
   métricas de negocio del sistema agéntico (Parte 2), cerrando el ciclo.

## 3. LLMOps (específico del componente conversacional, cuando se incorpore un LLM real)

- **Gestión de prompts como código**: versionados en el repositorio, con
  revisión de cambios igual que el resto del código (no editables en caliente
  sin control de versiones).
- **Evaluación continua**: set de conversaciones de referencia (ampliando
  los 13 escenarios de este prototipo) que se re-ejecutan en cada cambio de
  prompt o de modelo, con las mismas 26 pruebas automatizadas como piso
  mínimo no negociable.
- **Guardrails en capas**: (a) reglas de negocio determinísticas (nunca se
  delegan al LLM), (b) clasificador/heurística de riesgo previa a cada
  respuesta, (c) validación de salida antes de enviar (ver
  `guardrails.validar_respuesta_agente`), (d) monitoreo de costo/latencia
  por conversación.
- **Human-in-the-loop**: muestreo periódico de conversaciones cerradas para
  auditoría de calidad, no solo de las escaladas.

## 4. Seguridad y cumplimiento

- Todo identificador de cliente/obligación viaja enmascarado end-to-end
  (ya es la práctica de los datos entregados).
- Control de acceso por rol (RBAC) a la cola de escalamiento y a las trazas.
- Retención y cifrado de logs conforme a la política de datos personales del
  banco (Habeas Data, Colombia) — las trazas contienen fragmentos de
  conversación y deben tratarse como dato sensible.
- Plan de rollback inmediato: si el monitoreo detecta una tasa de ofertas no
  autorizadas > 0% o una caída abrupta de F1, el sistema puede revertir al
  modelo/version de reglas anterior sin intervención manual (feature flag).

## 5. Mantenimiento

- Dueño de producto único por componente (modelo y agéntico) con SLA de
  revisión de alertas.
- Revisión trimestral de los supuestos de negocio parametrizados (cooldowns,
  umbrales de auto-cura, prioridad de alternativas) con el área de política
  de cartera, ya que hoy son supuestos explícitos del prototipo, no
  aprendidos de datos.
