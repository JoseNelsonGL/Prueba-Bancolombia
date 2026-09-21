const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, TableOfContents, PageOrientation, LevelFormat,
  ExternalHyperlink,
} = require("docx");

const ASSETS = __dirname;
const NAVY = "1F3B57";
const BLUE = "34608D";
const GRAY = "555555";
const LIGHTGRAY = "F2F2F2";
const RED = "B03A2E";

const FONT = "Calibri";

function h(text, level, color = NAVY) {
  return new Paragraph({
    heading: level,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, bold: true, color, font: FONT })],
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 140 },
    children: Array.isArray(text)
      ? text
      : [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: FONT, size: 22 })],
  });
}

function cell(text, { header = false, width, shade } = {}) {
  return new TableCell({
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : header
      ? { type: ShadingType.CLEAR, fill: NAVY }
      : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({
        text: String(text), bold: header, font: FONT, size: 20,
        color: header ? "FFFFFF" : "000000",
      })],
    })],
  });
}

function table(headerRow, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headerRow.map((t, i) => cell(t, { header: true, width: colWidths[i] })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((t, i) => cell(t, { width: colWidths[i], shade: ri % 2 ? LIGHTGRAY : undefined })),
      })),
    ],
  });
}

const IMG_ASPECT = {
  "diagrama_pipeline_parte1.png": 935 / 1870,
  "diagrama_arquitectura_parte2.png": 1020 / 1870,
};

function image(file, widthPx = 620) {
  const buf = fs.readFileSync(path.join(ASSETS, file));
  const aspect = IMG_ASPECT[file] || 0.5;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 200 },
    children: [new ImageRun({
      data: buf, type: "png",
      transformation: { width: widthPx, height: Math.round(widthPx * aspect) },
    })],
  });
}

// ---------------------------------------------------------------------------

const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 420, hanging: 260 } } } }],
    }],
  },
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: NAVY, font: FONT },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: BLUE, font: FONT },
        paragraph: { spacing: { before: 260, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: "333333", font: FONT },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  sections: [
    // ---------------- PORTADA ----------------
    {
      properties: { page: { size: { width: 12240, height: 15840 } } },
      children: [
        new Paragraph({ spacing: { before: 2200 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "DOCUMENTO METODOLÓGICO", bold: true, size: 44, color: NAVY, font: FONT })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 240 },
          children: [new TextRun({
            text: "Modelo de Propensión a Aceptación de Opciones de Pago\ny Sistema Agéntico para la Gestión de Cartera en Mora",
            size: 28, color: BLUE, font: FONT,
          })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 700 },
          children: [new TextRun({ text: "Prueba Técnica — Bancolombia", size: 24, italics: true, color: GRAY, font: FONT })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 1400 },
          children: [new TextRun({ text: "Jose Nelson González", size: 24, bold: true, font: FONT })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 100 },
          children: [new TextRun({ text: "Septiembre de 2026", size: 22, color: GRAY, font: FONT })],
        }),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------- TABLA DE CONTENIDO ----------------
        h("Tabla de Contenido", HeadingLevel.HEADING_1),
        new TableOfContents("Tabla de Contenido", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------- 1. INTRODUCCIÓN ----------------
        h("1. Introducción y Contexto de Negocio", HeadingLevel.HEADING_1),
        p("Bancolombia gestiona un portafolio de crédito en el que un porcentaje de obligaciones entra en mora cada mes. Desde el primer día de mora se activan estrategias de gestión, entre ellas las opciones de pago (ampliación de plazo, reducción de cuota, renegociación de tasa, reestructuración) y los acuerdos de pago de gestión temprana (compromiso a máximo 5 días). Hoy la priorización de a quién gestionar se basa en exposición de la deuda y probabilidad de pago; el objetivo de esta prueba es incorporar, con un mes de anticipación, la probabilidad de que el cliente ACEPTE una opción de pago, y usarla dentro de un sistema de inteligencia artificial que decida y ejecute la siguiente mejor acción respetando las reglas de negocio."),
        p("Este documento consolida la metodología, las decisiones técnicas, los supuestos y los resultados de las dos partes de la prueba: (1) el modelo analítico de propensión y (2) el sistema agéntico de gestión proactiva y reactiva de clientes en mora."),

        // ---------------- 2. OBJETIVO ----------------
        h("2. Objetivo y Alcance", HeadingLevel.HEADING_1),
        bullet("Diseñar y desarrollar una solución analítica E2E que genere, por obligación, un indicador de propensión a aceptar una opción de pago en el mes siguiente, contemplando las etapas de MLOps."),
        bullet("Proponer e implementar un prototipo funcional de un sistema de agentes de IA coordinados que gestione proactiva y reactivamente a los clientes en mora, ofreciendo únicamente lo que la política de crédito autoriza."),
        bullet("Documentar metodología, supuestos, riesgos, pruebas y una propuesta de arquitectura de operación en producción para ambos componentes."),

        // ---------------- 3. CUERPO PRINCIPAL DEL DOCUMENTO TÉCNICO ----------------
        h("3. Documento Técnico — Cuerpo Principal", HeadingLevel.HEADING_1),
        p([new TextRun({ text: "Nota: esta sección corresponde al documento técnico exigido por el enunciado (máximo 4.000 caracteres, excluyendo anexos, imágenes y tablas). El resto del documento (secciones 4 a 9) son los anexos de soporte con el detalle metodológico completo.", italics: true, color: GRAY, size: 20, font: FONT })]),

        h("3.1 Parte 1 — Modelo de propensión", HeadingLevel.HEADING_2),
        p([new TextRun({ text: "Proceso: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "se recibieron 4 tablas (trtest, master_customer_data, probabilidad_oblig_hist, maestra_cuotas_pagos_mes_hist) y oot.csv (enero-2024, solo IDs). El EDA reveló el hallazgo central: la mayoría de columnas de trtest (gestiones, pagos, alternativa aplicada, mora fin de mes) describen el resultado del mismo mes a predecir → fuga de información si se usan tal cual. Se rediseñó el pipeline para usar solo información de t-1 hacia atrás (lags propios de la obligación, snapshot demográfico más reciente ≤ corte, scores históricos del banco), replicando el escenario real de pronosticar un mes antes.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Decisiones clave: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "LightGBM (categóricas/nulos nativos); validación temporal (train ago-nov 2023, valid dic-2023, no aleatoria); umbral optimizado para F1. Resultado con las 4 tablas integradas: AUC=0.729, F1=0.671 en validación (el historial de pagos fue la incorporación de mayor impacto).", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Supuestos: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "snapshot demográfico de dic-2023 usado como \"as-of\" para enero-2024 (el panel no llega a esa fecha); nulos demográficos (~40-50%) tratados como missing informativo, no imputados.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Riesgos/limitaciones: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "oot.csv no trae producto/banca/elegibilidad vigente, por lo que ~50% de sus obligaciones son \"cold start\" y dependen solo de demografía + scores del banco; el panel demográfico es disperso; no se validó estabilidad poblacional (PSI) trtest-vs-oot — queda como monitoreo de producción recomendado.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Dato adicional recomendado: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "un snapshot de elegibilidad/producto vigente al momento del scoring (ausente hoy en oot.csv) mejoraría el modelo para obligaciones nuevas; costo bajo, pues el motor de preaprobación ya genera esa información mensualmente.", font: FONT, size: 22 })]),

        h("3.2 Parte 2 — Sistema agéntico", HeadingLevel.HEADING_2),
        p([new TextRun({ text: "Arquitectura: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "patrón supervisor lineal y auditable — Contexto → Reglas de negocio (única fuente de verdad sobre qué ofrecer, determinística) → Siguiente Mejor Acción (integra el score de la Parte 1) → Conversacional → Guardrails → Escalamiento, con trazabilidad JSON por sesión. En un dominio regulado, la previsibilidad de un flujo lineal pesa más que la flexibilidad de un grafo de agentes libre.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Sin acceso a LLM en este entorno: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "intención y redacción se implementaron con reglas léxicas/plantillas, con punto de extensión explícito para reemplazar por un LLM real sin tocar el motor de reglas — el LLM redactaría, nunca decidiría qué ofrecer.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Pruebas: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "26 pruebas automatizadas (reglas de negocio, NBA, guardrails, integración end-to-end) + 13 escenarios simulados cubriendo los 7 casos pedidos más robustez (caída del servicio de scoring) y restricción jurídica dura. Umbral: 0% de ofertas no autorizadas y 0% de restricciones ignoradas (tolerancia cero).", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Riesgos: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "el NLU por reglas es frágil ante lenguaje real no anticipado; la priorización entre alternativas usa un orden fijo por severidad de mora (supuesto a validar), no aprendido de datos históricos de aceptación.", font: FONT, size: 22 })]),
        p([new TextRun({ text: "Conclusión general: ", bold: true, font: FONT, size: 22 }), new TextRun({ text: "ambos componentes son viables como prototipo demostrable dentro del alcance y tiempo de la prueba. El mayor riesgo de negocio no es el desempeño puntual del modelo sino la fuga de información si no se audita qué variables están realmente disponibles al momento de decidir — hallazgo válido tanto para la Parte 1 como para su integración con la Parte 2.", font: FONT, size: 22 })]),

        h("3.3 Declaración de Uso de IA Generativa", HeadingLevel.HEADING_2),
        p("Se usó Claude (Anthropic) como asistente de desarrollo de extremo a extremo: análisis exploratorio, identificación del riesgo de fuga de información, diseño del pipeline de features, entrenamiento del modelo, diseño de la arquitectura agéntica, e implementación de reglas/agentes/pruebas/documentación. El candidato dirigió el alcance, las decisiones de negocio (cooldowns, prioridades, qué construir dado el tiempo disponible) y revisó los resultados y supuestos antes de la entrega."),

        new Paragraph({ children: [new PageBreak()] }),
      ],
    },

    // ==================== ANEXO A ====================
    {
      properties: {},
      children: [
        h("4. Anexo A — Metodología Detallada (Parte 1)", HeadingLevel.HEADING_1),

        h("4.1 Datos disponibles", HeadingLevel.HEADING_2),
        table(
          ["Tabla", "Filas", "Periodo", "Llave"],
          [
            ["trtest.csv", "568.251", "Ago–Dic 2023", "nit#num_oblig_orig#num_oblig, mes"],
            ["master_customer_data.csv", "430.000", "Jul–Dic 2023 (panel)", "nit, año-mes"],
            ["probabilidad_oblig_hist.csv", "4.804.836", "Ene–Dic 2023 (panel)", "num_oblig, año-mes"],
            ["maestra_cuotas_pagos_mes_hist.csv", "4.855.035", "Ene–Dic 2023 (panel)", "num_oblig, año-mes"],
            ["oot.csv / sample_submission.csv", "112.549", "Enero 2024", "nit#num_oblig_orig#num_oblig"],
          ],
          [3200, 1600, 2600, 3000],
        ),

        h("4.2 Hallazgo crítico: fuga de información", HeadingLevel.HEADING_2),
        p("La mayoría de las columnas de trtest.csv (cant_gestiones, pago_mes, porc_pago_mes, marca_alternativa, dias_mora_fin, saldo_capital, entre otras) describen eventos ocurridos DURANTE el mismo mes de la variable respuesta: son consecuencia o coocurrencia directa de la decisión que se quiere predecir. Usarlas como variables contemporáneas habría producido un modelo con métricas artificialmente altas en validación, pero inútil en producción, porque esa información no existe todavía cuando hay que emitir el pronóstico un mes antes."),
        p("Decisión metodológica: estas columnas se usan únicamente como fuente de variables rezagadas (estado de la obligación en el mes t-1), nunca en su versión del mes t. Se conservan como contemporáneas solo las que describen la oferta/elegibilidad vigente (banca, segmento, producto, cantidad de alternativas preaprobadas) — aunque estas tampoco existen en oot.csv, por lo que el modelo final usa el subconjunto de 76 variables presentes en ambos mundos."),

        image("diagrama_pipeline_parte1.png", 620),

        h("4.3 Variables y tratamiento de calidad de datos", HeadingLevel.HEADING_2),
        bullet("fecha_corte de maestra_cuotas_pagos_mes_hist viene en formato YYYYMMDD (no YYYYMM); se normalizó."),
        bullet("porc_pago traía valores infinitos por división entre cuota=0; se limpiaron y se capó a 1000%."),
        bullet("~20% de los clientes de trtest nunca aparecen en master_customer_data; el resto tiene cobertura dispersa (promedio 1,78 snapshots en 6 meses) → nulos demográficos del 37-50%, tratados como missing informativo más una bandera tiene_snapshot_demografico."),
        bullet("edad_cli contiene valores inválidos (0 y 123 años) reportados como hallazgo de calidad de datos, no corregidos por no afectar la variable de forma determinante dado el manejo nativo de nulos/outliers de LightGBM."),

        h("4.4 Validación y resultados", HeadingLevel.HEADING_2),
        p("Split temporal (no aleatorio): entrenamiento con agosto-noviembre 2023, validación con diciembre 2023, replicando el escenario real de predecir el mes siguiente. Umbral de decisión optimizado para F1 (0.325), en vez de 0.5 por defecto."),
        table(
          ["Métrica", "Valor"],
          [
            ["AUC (validación dic-2023)", "0.729"],
            ["F1 (validación dic-2023)", "0.671"],
            ["Precisión", "0.551"],
            ["Recall", "0.859"],
            ["Observaciones de entrenamiento / validación", "467.785 / 100.466"],
            ["Variables utilizadas", "76"],
          ],
          [5200, 2600],
        ),

        h("4.5 Variables más importantes (top 12, por ganancia)", HeadingLevel.HEADING_2),
        table(
          ["Variable", "Descripción breve"],
          [
            ["marca_pago_prev", "Tipo de pago realizado el mes anterior (más/menos/igual/no pagó)"],
            ["prob_propension_prev", "Score actual del banco: probabilidad de pago el mes siguiente"],
            ["cuota_prev", "Valor de la cuota del mes anterior"],
            ["prob_alrt_temprana_prev", "Score actual del banco: probabilidad de entrar en mora"],
            ["porc_pago_mean_3m", "Promedio de cumplimiento de pago en los últimos 3 meses"],
            ["prob_auto_cura_prev", "Score actual del banco: probabilidad de autocorrección"],
            ["prev_var_rpta_alt", "Si aceptó una opción de pago el mes anterior"],
            ["prev_marca_alternativa_orig", "Si aceptó originalmente una alternativa el mes anterior"],
            ["porc_pago_prev", "Porcentaje de pago de la cuota del mes anterior"],
            ["nombre_dpto_dirp", "Departamento de vinculación del cliente"],
            ["ciiu", "Actividad económica del cliente"],
            ["prev_dias_mora_fin", "Días de mora al cierre del mes anterior"],
          ],
          [3000, 5800],
        ),

        h("4.6 Cumplimiento de criterios de MLOps", HeadingLevel.HEADING_2),
        table(
          ["Etapa MLOps", "Implementación propuesta"],
          [
            ["Preparación de datos", "Feature store con lógica punto-en-el-tiempo (paridad train/serve); validación de calidad con Great Expectations/pandera."],
            ["Entrenamiento", "LightGBM + validación temporal; tracking de experimentos con MLflow; registro con etapas Staging/Production."],
            ["Inferencia", "Batch mensual (alimenta la priorización por lotes) + endpoint on-demand (consultado por el sistema agéntico), ambos reutilizando el mismo pipeline de features."],
            ["Productización", "Contenedor Docker versionado por commit; contrato de datos explícito; pruebas de contrato en CI."],
            ["Despliegue continuo", "CI (lint + pruebas + smoke retrain) y CD con evaluación shadow contra el modelo en producción antes de promover; despliegue canario."],
            ["Monitoreo", "Deriva de datos (PSI/KS), deriva de desempeño (F1/AUC real vs. esperado), calidad de servicio (latencia, cobertura de features), dashboards y alertas."],
          ],
          [2400, 6400],
        ),

        new Paragraph({ children: [new PageBreak()] }),
      ],
    },

    // ==================== ANEXO B ====================
    {
      properties: {},
      children: [
        h("5. Anexo B — Arquitectura del Sistema Agéntico (Parte 2)", HeadingLevel.HEADING_1),

        h("5.1 Filosofía de diseño", HeadingLevel.HEADING_2),
        p("Cobranza es un dominio regulado: cada oferta debe ser exactamente la que la política de crédito autoriza, debe quedar trazada, y debe poder explicarse. Por eso se separa deliberadamente QUÉ se puede ofrecer (determinístico, motor de reglas, nunca delegado a un modelo de lenguaje) de CÓMO se comunica (lenguaje natural). Se eligió un patrón supervisor lineal y auditable en lugar de un grafo de agentes de diálogo libre: para este dominio, la previsibilidad pesa más que la flexibilidad."),

        image("diagrama_arquitectura_parte2.png", 620),

        h("5.2 Agentes y responsabilidades", HeadingLevel.HEADING_2),
        table(
          ["Agente", "Responsabilidad"],
          [
            ["Contexto", "Ensambla el estado de la obligación: datos del cliente, mora, alternativas preaprobadas, historial y scores (Parte 1 + scores actuales del banco)."],
            ["Elegibilidad (reglas de negocio)", "Única fuente de verdad de qué se puede ofrecer: máx. 3 opciones/mes, cooldown 3-4 meses, bloqueo si ya hay opción vigente, restricciones duras."],
            ["Siguiente Mejor Acción (NBA)", "Decide la acción concreta combinando elegibilidad + score de propensión + señales del banco (auto-cura, alerta temprana)."],
            ["Conversacional", "Redacta el mensaje y conduce el diálogo dentro de lo autorizado; interpreta intención del cliente."],
            ["Guardrails", "Defensa en profundidad: detecta manipulación, señales sensibles, información contradictoria; valida la respuesta final."],
            ["Escalamiento", "Punto único de handoff a gestor humano con el contexto completo."],
            ["Trazabilidad", "Registra cada decisión de cada agente en un log estructurado por sesión."],
          ],
          [2600, 6200],
        ),

        h("5.3 Reglas de negocio clave", HeadingLevel.HEADING_2),
        bullet("Máximo 3 opciones de pago preaprobadas por obligación/mes."),
        bullet("Cooldown de 3 meses (ampliación de plazo, reducción de cuota) o 4 meses (renegociación de tasa, reestructuración) tras aplicar una alternativa, antes de poder ofrecer otra (supuesto parametrizable)."),
        bullet("Si el cliente ya aceptó una opción de pago vigente, no se ofrece ninguna alternativa nueva ni acuerdo de pago."),
        bullet("Acuerdo de pago (compromiso a máximo 5 días) solo en gestión temprana (mora ≤ 90 días) y sin restricciones activas."),
        bullet("Cualquier restricción dura (jurídico, fraude, etc.) bloquea toda oferta y escala siempre a un gestor humano."),

        h("5.4 Integración con el modelo analítico (Parte 1)", HeadingLevel.HEADING_2),
        p("El score de propensión entra al Agente de Contexto como un campo más, obtenido del endpoint de inferencia. El NBA lo usa para: decidir si vale la pena contactar proactivamente, priorizar entre varias alternativas elegibles, y —junto con la probabilidad de auto-cura— diferir gestión intensa en mora muy temprana con alta probabilidad de autocorrección. El sistema es robusto a que este score no esté disponible: las reglas de negocio siguen operando de forma determinística (validado en pruebas de robustez, sección 6.1)."),

        h("5.5 Seguridad, trazabilidad y escalamiento", HeadingLevel.HEADING_2),
        bullet("Todos los identificadores llegan enmascarados; el prototipo usa únicamente perfiles ficticios."),
        bullet("Barrera de salida: valida que la respuesta generada nunca mencione una alternativa no autorizada, sin importar qué la generó."),
        bullet("Cada sesión tiene un session_id; cada decisión de cada agente queda registrada con timestamp y motivo (explicabilidad no post-hoc)."),
        bullet("Restricciones duras, señales sensibles, manipulación, información contradictoria e incumplimiento admitido de un acuerdo previo, escalan siempre a un gestor humano."),

        new Paragraph({ children: [new PageBreak()] }),
      ],
    },

    // ==================== ANEXO C ====================
    {
      properties: {},
      children: [
        h("6. Anexo C — Pruebas y Validación del Sistema Agéntico", HeadingLevel.HEADING_1),

        h("6.1 Pruebas automatizadas (pytest)", HeadingLevel.HEADING_2),
        p("26 pruebas, 100% pasan, organizadas en 4 capas:"),
        table(
          ["Capa", "# pruebas", "Qué garantizan"],
          [
            ["Reglas de negocio", "6", "Máx. 3 opciones/mes, cooldown respetado y liberado a tiempo, bloqueo si ya hay opción vigente, restricción dura siempre escala."],
            ["NBA", "4", "Priorización correcta según mora, diferimiento por auto-cura, robustez ante caída del servicio de scoring."],
            ["Guardrails (seguridad)", "5", "Detección de manipulación, señales sensibles, información contradictoria; cero falsos positivos en mensaje neutro."],
            ["Integración end-to-end", "4", "Cliente no elegible nunca recibe oferta; restricción jurídica escala sin ofrecer; manipulación detiene el flujo; regresión de reasignación de alternativa."],
          ],
          [2400, 1200, 5200],
        ),

        h("6.2 Escenarios funcionales simulados (13)", HeadingLevel.HEADING_2),
        p("Cubren explícitamente los 7 casos pedidos en el enunciado más 2 de robustez/seguridad. Perfiles y conversaciones 100% ficticios."),
        table(
          ["#", "Escenario", "Resultado"],
          [
            ["1", "Mora temprana + alta probabilidad de pago", "Ofrece acuerdo de pago a 5 días"],
            ["2", "Elegible para varias opciones de pago", "Prioriza y explica una alternativa"],
            ["3", "No elegible / cooldown activo", "Sin ofertas (monitoreo)"],
            ["4a", "Rechaza la propuesta", "Registra rechazo, no insiste"],
            ["4b", "Pide otra alternativa", "Ofrece la siguiente elegible y registra la correcta al aceptar"],
            ["4c", "Incumple acuerdo previo", "Escala a gestor humano"],
            ["5a", "Contacto reactivo: consulta de saldo", "Responde directamente"],
            ["5b", "Contacto reactivo: dificultad financiera", "Escala por señal sensible"],
            ["6", "Información contradictoria", "Escala para verificación humana"],
            ["7a", "Solicitud sensible (riesgo personal)", "Escala de inmediato"],
            ["7b", "Intento de manipulación", "Bloquea y escala"],
            ["8", "Restricción jurídica dura", "Escala directo, cero contacto"],
            ["9", "Servicio de scoring caído", "Sigue operando con reglas de negocio"],
          ],
          [700, 4200, 3900],
        ),

        h("6.3 Métricas y umbrales de aceptación propuestos para producción", HeadingLevel.HEADING_2),
        table(
          ["Métrica", "Umbral propuesto"],
          [
            ["Tasa de ofertas no autorizadas", "0% (bloqueo automático, no solo alerta)"],
            ["Precisión del escalamiento", "≥ 85% confirmado como necesario por un humano"],
            ["Recall de señales sensibles", "≥ 95% (el falso negativo es el error costoso)"],
            ["Tiempo a escalamiento", "< 5 segundos"],
            ["Cobertura de intención (no ambiguo)", "≥ 80%"],
          ],
          [4200, 4600],
        ),

        h("6.4 Oportunidades de mejora identificadas", HeadingLevel.HEADING_2),
        bullet("Reemplazar el NLU basado en reglas léxicas por un LLM con salida estructurada, manteniendo las reglas de negocio como red de seguridad, no como reemplazo."),
        bullet("Aprender la priorización entre alternativas elegibles de datos históricos de aceptación por segmento, en vez del orden fijo actual por severidad de mora."),
        bullet("Incorporar pruebas de carga/concurrencia, fuera del alcance de este prototipo."),

        new Paragraph({ children: [new PageBreak()] }),
      ],
    },

    // ==================== ANEXO D + E + repo ====================
    {
      properties: {},
      children: [
        h("7. Anexo D — Arquitectura de Producción y Operación (Propuesta)", HeadingLevel.HEADING_1),
        p("Visión end-to-end, independiente de proveedor cloud: ingesta y features (feature store con lógica punto-en-el-tiempo) → entrenamiento/registro (MLflow, con aprobación de promoción por comparación shadow) → scoring batch mensual (alimenta la priorización por lotes existente) y on-demand (consultado por el sistema agéntico) → orquestador agéntico (reglas → NBA → conversacional → guardrails) → cola de escalamiento humano con contexto completo → observabilidad (deriva de datos/desempeño, tasa de ofertas no autorizadas, LLMOps del componente conversacional cuando se incorpore un LLM real)."),
        bullet("Seguridad: identificadores enmascarados end-to-end, RBAC sobre la cola de escalamiento y las trazas, cifrado y retención conforme a Habeas Data."),
        bullet("Plan de rollback: reversión automática a la versión anterior del modelo/reglas si el monitoreo detecta ofertas no autorizadas > 0% o caída abrupta de F1 (feature flag)."),
        bullet("Mantenimiento: dueño de producto por componente, con revisión trimestral de los supuestos de negocio parametrizados (cooldowns, umbrales, prioridades) junto con el área de política de cartera."),

        h("8. Anexo E — Declaración de Uso de IA Generativa (detalle)", HeadingLevel.HEADING_1),
        p("Herramienta utilizada: Claude (Anthropic), a través de Claude Code/Cowork, durante toda la prueba."),
        table(
          ["Actividad", "Rol de la IA generativa", "Rol del candidato"],
          [
            ["Análisis exploratorio de datos", "Ejecución de código de exploración y detección del hallazgo de fuga de información", "Validación del hallazgo y su relevancia para el negocio"],
            ["Diseño del pipeline de features", "Propuesta e implementación del diseño \"as-of\" sin fuga", "Revisión de la lógica y de los supuestos de cooldown/ventanas"],
            ["Entrenamiento y evaluación del modelo", "Implementación, ejecución y reporte de métricas", "Definición del criterio de éxito (F1) y revisión de resultados"],
            ["Arquitectura y código del sistema agéntico", "Diseño de agentes, reglas, guardrails, pruebas e implementación", "Definición de reglas de negocio, alcance y priorización dado el tiempo disponible"],
            ["Documentación", "Redacción de todos los documentos (este incluido)", "Revisión, ajuste y validación del contenido antes de la entrega"],
          ],
          [2400, 3200, 2800],
        ),
        p("Ninguna sección de este documento fue tomada de fuentes externas sin adaptación al contexto específico de esta prueba; todo el código fue ejecutado y verificado antes de incluirse en la entrega."),

        h("9. Estructura del Repositorio y Reproducibilidad", HeadingLevel.HEADING_1),
        p("El repositorio Git entregado contiene:"),
        bullet("src/ — pipeline de datos (data_prep.py) y entrenamiento/inferencia (train.py) de la Parte 1."),
        bullet("agentic/ — modelos, reglas de negocio, NBA, guardrails, conversacional, orquestador y escenarios simulados de la Parte 2."),
        bullet("tests/ — 26 pruebas automatizadas (pytest)."),
        bullet("docs/ — este documento y sus fuentes en Markdown (documento_tecnico.md, eda_notas.md, mlops_parte1.md, arquitectura_agentica.md, pruebas_agentico.md, arquitectura_produccion.md, presentacion_ejecutiva.md)."),
        bullet("results/ — resultado_prueba.csv, métricas, importancia de variables y trazas de las sesiones agénticas."),
        p("Instrucciones de reproducción completas en README.md del repositorio."),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ASSETS, "..", "Documento_Metodologico_Prueba_Bancolombia.docx");
  fs.writeFileSync(out, buf);
  console.log("Escrito:", out);
});
