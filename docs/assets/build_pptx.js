// Genera docs/Presentacion_Ejecutiva_Prueba_Bancolombia.pptx a partir del
// guion en docs/presentacion_ejecutiva.md, con material real del proyecto
// (funnel de variables, ROC, SHAP, diagrama de arquitectura, distribución
// de la prueba masiva). Material NO obligatorio de entregar (ver nota en
// ese archivo) -- se construye como cortesía para que Jose solo tenga que
// practicar la sustentación, no diseñar. 10 slides, revisión v2 con Jose.
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const path = require("path");

// ---------------------------------------------------------------------
// Paleta: "Midnight Executive" + un acento cálido para números/hitos.
// ---------------------------------------------------------------------
const NAVY = "1E2761";
const NAVY_DARK = "141A47";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const LIGHTBG = "EEF2FB";
const TEXT = "1E2761";
const MUTED = "5B6B8C";
const ACCENT = "E8A33D"; // ámbar cálido, único acento "fuerte"
const GREEN = "3F8F5F"; // verde discreto, solo para puntos de semáforo
const FONT = "Calibri";
const FONT_HEAD = "Cambria";

const ASSETS = path.join(__dirname); // docs/assets
const NB = path.join(__dirname, "..", "..", "notebooks"); // notebooks/

async function icon(IconComp, color, sizePx = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComp, { color: `#${color}`, size: sizePx })
  );
  const buf = await sharp(Buffer.from(svg)).resize(sizePx, sizePx).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3" x 7.5"
  pres.author = "Jose Nelson Gonzalez";
  pres.company = "Mission SAS";
  pres.title = "Prueba Técnica Bancolombia — Modelo de Propensión y Sistema Agéntico";

  const W = 13.33, H = 7.5;

  // Pre-render icons used across slides
  const ic = {
    contexto: await icon(fa.FaBullseye, WHITE),
    modelo: await icon(fa.FaChartLine, WHITE),
    agente: await icon(fa.FaRobot, WHITE),
    produccion: await icon(fa.FaCloud, WHITE),
    comite: await icon(fa.FaUsers, WHITE),
    database: await icon(fa.FaDatabase, NAVY),
    filtro: await icon(fa.FaFilter, NAVY),
    reloj: await icon(fa.FaClock, NAVY),
    calendario: await icon(fa.FaCalendarAlt, NAVY),
    alerta: await icon(fa.FaExclamationTriangle, NAVY),
    balanza: await icon(fa.FaBalanceScale, WHITE),
    cerebro: await icon(fa.FaBrain, WHITE),
    chat: await icon(fa.FaCommentDots, WHITE),
    escudo: await icon(fa.FaShieldAlt, WHITE),
    persona: await icon(fa.FaUserTie, WHITE),
    check: await icon(fa.FaCheckCircle, NAVY),
    flask: await icon(fa.FaFlask, NAVY),
    sync: await icon(fa.FaSyncAlt, NAVY),
    mapa: await icon(fa.FaMapSigns, NAVY),
    prohibido: await icon(fa.FaBan, WHITE),
    escudoAmbar: await icon(fa.FaShieldAlt, ACCENT),
    alertaAmbar: await icon(fa.FaExclamationTriangle, ACCENT),
    balanzaAmbar: await icon(fa.FaBalanceScale, ACCENT),
    apreton: await icon(fa.FaHandshake, WHITE),
    checkBlanco: await icon(fa.FaCheckCircle, WHITE),
    gauge: await icon(fa.FaTachometerAlt, WHITE),
  };

  const darkBg = { color: NAVY_DARK };
  const lightBg = { color: WHITE };
  const tintBg = { color: LIGHTBG };

  // -----------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------
  function title(slide, text, opts = {}) {
    slide.addText(text, {
      x: 0.6, y: opts.y ?? 0.6, w: opts.w ?? 12.1, h: opts.h ?? 0.9,
      fontFace: FONT_HEAD, fontSize: opts.size ?? 30, bold: true,
      color: opts.color ?? NAVY, isTextBox: true, margin: 0, valign: "top",
    });
  }

  function iconCircle(slide, imgData, x, y, d, bgColor) {
    slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: bgColor }, line: { type: "none" } });
    const pad = d * 0.26;
    slide.addImage({ data: imgData, x: x + pad / 2, y: y + pad / 2, w: d - pad, h: d - pad });
  }

  function dot(slide, x, y, d, color) {
    slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color }, line: { type: "none" } });
  }

  function pageNum(slide, n) {
    slide.addText(String(n), {
      x: W - 0.9, y: H - 0.55, w: 0.5, h: 0.35,
      fontFace: FONT, fontSize: 10, color: MUTED, align: "right",
      isTextBox: true, margin: 0,
    });
  }

  // ===================================================================
  // 1. PORTADA
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = darkBg;
    s.addShape("ellipse", { x: 9.8, y: -2.2, w: 6, h: 6, fill: { color: NAVY }, line: { type: "none" } });
    s.addShape("ellipse", { x: 11.6, y: 4.3, w: 4, h: 4, fill: { color: NAVY }, line: { type: "none" } });

    s.addText("PRUEBA TÉCNICA · BANCOLOMBIA", {
      x: 0.9, y: 1.6, w: 10, h: 0.4, fontFace: FONT, fontSize: 13, bold: true,
      charSpacing: 3, color: ACCENT, isTextBox: true, margin: 0,
    });
    s.addText("Modelo de Propensión a Aceptación\nde Opciones de Pago + Sistema Agéntico", {
      x: 0.9, y: 2.1, w: 11.2, h: 2.1, fontFace: FONT_HEAD, fontSize: 40, bold: true,
      color: WHITE, isTextBox: true, margin: 0, lineSpacing: 46,
    });
    s.addText("Gestión proactiva y reactiva de cartera en mora", {
      x: 0.9, y: 4.15, w: 10, h: 0.5, fontFace: FONT, fontSize: 18, italic: true,
      color: ICE, isTextBox: true, margin: 0,
    });

    s.addShape("line", { x: 0.9, y: 5.85, w: 2.2, h: 0, line: { color: ACCENT, width: 2 } });
    s.addText("Jose Nelson González", {
      x: 0.9, y: 6.05, w: 8, h: 0.4, fontFace: FONT, fontSize: 14, bold: true,
      color: WHITE, isTextBox: true, margin: 0,
    });
    s.addText("Sustentación técnica y ejecutiva", {
      x: 0.9, y: 6.45, w: 8, h: 0.35, fontFace: FONT, fontSize: 12,
      color: ICE, isTextBox: true, margin: 0,
    });
    s.addNotes("Portada. Presentarse brevemente y anunciar la estructura.");
  }

  // ===================================================================
  // 2. AGENDA
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Agenda", { y: 0.75, h: 0.9 });

    const items = [
      { ic: ic.contexto, t: "Contexto y objetivo", d: "1 min", sub: "Por qué anticipar la aceptación de opciones de pago" },
      { ic: ic.modelo, t: "Parte 1 — Modelo de propensión", d: "3 min", sub: "Metodología, comparación de modelos y resultado" },
      { ic: ic.agente, t: "Parte 2 — Sistema agéntico", d: "4 min", sub: "Arquitectura, reglas de negocio y pruebas" },
      { ic: ic.produccion, t: "Producción y monitoreo", d: "2 min", sub: "Arquitectura de operación y qué se mide para detectar problemas a tiempo" },
      { ic: ic.comite, t: "Resumen ejecutivo", d: "5 min", sub: "Resultado de negocio, alcance, riesgos y pedido de aprobación" },
    ];
    let y = 2.05;
    const rowH = 0.92;
    items.forEach((it, i) => {
      const bg = i === items.length - 1 ? ACCENT : NAVY;
      iconCircle(s, it.ic, 0.7, y, 0.66, bg);
      s.addText(it.t, {
        x: 1.6, y: y - 0.03, w: 7.6, h: 0.4, fontFace: FONT_HEAD, fontSize: 17, bold: true,
        color: NAVY, isTextBox: true, margin: 0,
      });
      s.addText(it.sub, {
        x: 1.6, y: y + 0.36, w: 8.9, h: 0.35, fontFace: FONT, fontSize: 11.5, italic: true,
        color: MUTED, isTextBox: true, margin: 0,
      });
      s.addText(it.d, {
        x: 10.9, y: y + 0.1, w: 1.7, h: 0.4, fontFace: FONT, fontSize: 14, bold: true,
        color: bg === ACCENT ? ACCENT : NAVY, align: "right", isTextBox: true, margin: 0,
      });
      if (i < items.length - 1) {
        s.addShape("line", { x: 0.7, y: y + rowH - 0.08, w: 11.9, h: 0, line: { color: ICE, width: 1 } });
      }
      y += rowH;
    });
    pageNum(s, 2);
    s.addNotes("Recorrer la agenda en 15-20 segundos, sin detenerse en cada punto.");
  }

  // ===================================================================
  // 3. CONTEXTO Y OBJETIVO
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "De priorizar por exposición a priorizar por propensión");

    s.addShape("roundRect", { x: 0.6, y: 2.15, w: 5.9, h: 4.35, rectRadius: 0.12, fill: { color: LIGHTBG }, line: { type: "none" } });
    s.addText("Hoy", { x: 0.95, y: 2.4, w: 5, h: 0.4, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: MUTED, isTextBox: true, margin: 0 });
    s.addText(
      "La cartera en mora se gestiona priorizando principalmente por monto de exposición. Las opciones de pago y los acuerdos son las palancas disponibles, pero se ofrecen sin saber de antemano qué tan receptivo será cada cliente.",
      { x: 0.95, y: 2.85, w: 5.2, h: 3.2, fontFace: FONT, fontSize: 14, color: TEXT, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25 }
    );

    s.addShape("roundRect", { x: 6.83, y: 2.15, w: 5.9, h: 4.35, rectRadius: 0.12, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Con este proyecto", { x: 7.18, y: 2.4, w: 5, h: 0.4, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText(
      "Un modelo anticipa, con un mes de antelación, la probabilidad de que cada cliente acepte una opción de pago. Un sistema agéntico automatiza el ofrecimiento de esa opción, respetando siempre las reglas de negocio vigentes.",
      { x: 7.18, y: 2.85, w: 5.2, h: 3.2, fontFace: FONT, fontSize: 14, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25 }
    );
    pageNum(s, 3);
    s.addNotes("Frase ancla: 'anticipar un mes antes la probabilidad de aceptación para priorizar mejor la gestión, y automatizar el ofrecimiento respetando reglas de negocio'.");
  }

  // ===================================================================
  // 4. PARTE 1 — Datos, variables y ventanas temporales
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Datos, decisión sobre variables y ventanas temporales", { size: 27 });

    // Funnel real del EDA
    const funnelW = 7.35, funnelH = funnelW / 2.0909;
    s.addShape("roundRect", { x: 0.6, y: 1.85, w: funnelW + 0.3, h: funnelH + 0.3, rectRadius: 0.08, fill: { color: LIGHTBG }, line: { type: "none" } });
    s.addImage({ path: path.join(NB, "eda_outputs", "02_embudo_variables.png"), x: 0.75, y: 2.0, w: funnelW, h: funnelH });
    s.addText("Se excluyen las columnas que describen el resultado del mismo mes (no disponibles en oot.csv) y se agregan lags propios, demografía, scores del banco e historial de pagos.", {
      x: 0.6, y: 2.0 + funnelH + 0.35, w: funnelW + 0.3, h: 1.0, fontFace: FONT, fontSize: 11.5, italic: true, color: MUTED, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });

    // Ventanas temporales
    const rx = 8.55, rw = 4.18;
    s.addText("Ventanas temporales", { x: rx, y: 1.85, w: rw, h: 0.4, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const windows = [
      { t: "Entrenamiento", r: "Ago 2023 – Nov 2023", d: "4 meses de historia" },
      { t: "Validación", r: "Dic 2023", d: "Elección de umbral (F1)" },
      { t: "OOT — la que se evalúa", r: "Ene 2024", d: "oot.csv entregado, solo IDs" },
    ];
    let wy = 2.4;
    windows.forEach((wdw) => {
      iconCircle(s, ic.calendario, rx, wy, 0.56, LIGHTBG);
      s.addText(wdw.t, { x: rx + 0.72, y: wy - 0.04, w: rw - 0.72, h: 0.32, fontFace: FONT_HEAD, fontSize: 13.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      s.addText(wdw.r, { x: rx + 0.72, y: wy + 0.27, w: rw - 0.72, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
      s.addText(wdw.d, { x: rx + 0.72, y: wy + 0.57, w: rw - 0.72, h: 0.3, fontFace: FONT, fontSize: 10.5, italic: true, color: MUTED, isTextBox: true, margin: 0 });
      wy += 1.02;
    });
    s.addShape("roundRect", { x: rx, y: wy + 0.05, w: rw, h: 1.15, rectRadius: 0.08, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Validación temporal, no aleatoria: se entrena con meses anteriores y se valida con el último mes disponible, igual que en producción.", {
      x: rx + 0.22, y: wy + 0.18, w: rw - 0.44, h: 0.9, fontFace: FONT, fontSize: 11, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.2,
    });
    pageNum(s, 4);
    s.addNotes("La mayoría de columnas de trtest describen el resultado del mismo mes; por eso no sirven para predecir el mes siguiente sin fuga. OOT = enero-2024, la única que se evalúa realmente.");
  }

  // ===================================================================
  // 5. PARTE 1 — Modelos evaluados y resultado
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = tintBg;
    title(s, "Se evaluaron 3 modelos; gana LightGBM por AUC, F1 y menor sobreajuste", { size: 22 });

    // ROC + tabla comparativa (columna izquierda)
    const leftCardX = 0.6, leftCardW = 7.28;
    const rocW = leftCardW - 0.2, rocH = rocW / 2.364;
    s.addShape("roundRect", { x: leftCardX, y: 1.65, w: leftCardW, h: rocH + 0.2, rectRadius: 0.06, fill: { color: WHITE }, line: { type: "none" } });
    s.addImage({ path: path.join(NB, "model_outputs", "roc_comparacion.png"), x: leftCardX + 0.1, y: 1.75, w: rocW, h: rocH });

    const tblY = 1.65 + rocH + 0.4;
    s.addTable(
      [
        [
          { text: "Modelo", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 11 } },
          { text: "AUC valid.", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 11, align: "center" } },
          { text: "F1 valid.", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 11, align: "center" } },
          { text: "Brecha train–valid", options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 11, align: "center" } },
        ],
        [
          { text: "LightGBM ✓", options: { bold: true, color: NAVY, fill: { color: LIGHTBG }, fontSize: 11 } },
          { text: "0.729", options: { color: TEXT, fill: { color: LIGHTBG }, fontSize: 11, align: "center" } },
          { text: "0.671", options: { color: TEXT, fill: { color: LIGHTBG }, fontSize: 11, align: "center" } },
          { text: "0.053", options: { color: TEXT, fill: { color: LIGHTBG }, fontSize: 11, align: "center" } },
        ],
        [
          { text: "Random Forest", options: { color: TEXT, fill: { color: WHITE }, fontSize: 11 } },
          { text: "0.705", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
          { text: "0.660", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
          { text: "0.025", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
        ],
        [
          { text: "Regresión Logística", options: { color: TEXT, fill: { color: WHITE }, fontSize: 11 } },
          { text: "0.685", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
          { text: "0.649", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
          { text: "0.022", options: { color: MUTED, fill: { color: WHITE }, fontSize: 11, align: "center" } },
        ],
      ],
      { x: leftCardX, y: tblY, w: leftCardW, colW: [2.28, 1.7, 1.7, 1.6], rowH: 0.32, border: { type: "solid", color: ICE, pt: 0.75 }, autoPage: false }
    );
    s.addText(
      "Criterio de selección: mayor F1 en validación (métrica de la prueba) y AUC, con la menor brecha train–valid posible (mide sobreajuste). LightGBM gana en las tres.\nPrincipal limitación: oot.csv no trae elegibilidad/producto vigente → ~50% de las obligaciones de enero-2024 son “cold start”.",
      { x: leftCardX, y: tblY + 1.28 + 0.15, w: leftCardW, h: 0.85, fontFace: FONT, fontSize: 10, italic: true, color: MUTED, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.2 }
    );

    // SHAP (columna derecha, altura completa, sin tocar la columna izquierda)
    const rightCardH = 5.35;
    const shapH = rightCardH - 0.24, shapW = shapH * 0.843;
    const rightCardW = shapW + 0.24;
    const rightCardX = W - 0.6 - rightCardW;
    s.addShape("roundRect", { x: rightCardX, y: 1.65, w: rightCardW, h: rightCardH, rectRadius: 0.06, fill: { color: WHITE }, line: { type: "none" } });
    s.addImage({ path: path.join(NB, "model_outputs", "shap_summary.png"), x: rightCardX + 0.12, y: 1.77, w: shapW, h: shapH });
    pageNum(s, 5);
    s.addNotes("ROC + brecha train/valid muestran por qué gana LightGBM. SHAP: historial de pagos y propensión previa dominan la explicación.");
  }

  // ===================================================================
  // 6. PARTE 2 — Cómo decide el agente, paso a paso
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Cómo decide el agente, paso a paso", { y: 0.55 });

    const diagW = 9.6, diagH = diagW / 1.667;
    const diagX = (W - diagW) / 2;
    s.addImage({ path: path.join(ASSETS, "diagrama_arquitectura_parte2.png"), x: diagX, y: 1.45, w: diagW, h: diagH });

    s.addText("Por qué separadas del LLM: en cobranza, la oferta debe ser exactamente la autorizada — nunca delegable a que un modelo de lenguaje la “invente”.", {
      x: 0.6, y: 1.45 + diagH + 0.15, w: 12.1, h: 0.6, align: "center", fontFace: FONT, fontSize: 13.5, italic: true, color: NAVY, isTextBox: true, margin: 0, lineSpacingMultiple: 1.2,
    });
    pageNum(s, 6);
    s.addNotes("Recorrer el diagrama con el puntero: elegibilidad decide QUÉ se puede ofrecer, NBA decide cuál priorizar, guardrails valida antes de enviar, y todo queda trazado.");
  }

  // ===================================================================
  // 7. PARTE 2 — Pruebas: dirigidas y masivas
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Probado a fondo: 49 pruebas, dos lógicas complementarias", { size: 25 });

    // Columna izquierda: dirigidas
    s.addText("Dirigidas — 42 pruebas escritas a mano", { x: 0.6, y: 1.75, w: 6.3, h: 0.4, fontFace: FONT_HEAD, fontSize: 15.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const capas = [
      { t: "Reglas de negocio (8)", d: "Máx. 3 opciones/mes, cooldowns, restricción dura, incumplimiento reciente" },
      { t: "Siguiente Mejor Acción (5)", d: "Priorización por mora, diferimiento, robustez si cae el scoring" },
      { t: "Guardrails de seguridad (9)", d: "Manipulación, señales sensibles, info. contradictoria, tokens filtrados" },
      { t: "NLU por reglas (5)", d: "Clasifica: acepta, rechaza, otra alternativa, saldo, dificultad" },
      { t: "Agente conversacional (8)", d: "Valida la respuesta completa, no solo la etiqueta de intención" },
      { t: "Integración orquestador (7)", d: "Flujo cliente→sistema de punta a punta, casos límite" },
    ];
    let cy = 2.25;
    capas.forEach((c) => {
      dot(s, 0.65, cy + 0.09, 0.12, NAVY);
      s.addText(c.t, { x: 0.95, y: cy - 0.05, w: 5.9, h: 0.3, fontFace: FONT, fontSize: 12.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      s.addText(c.d, { x: 0.95, y: cy + 0.24, w: 5.9, h: 0.35, fontFace: FONT, fontSize: 10.3, color: MUTED, isTextBox: true, margin: 0 });
      cy += 0.685;
    });

    // Columna derecha: masivas + chart
    s.addText("Masivas — 400 casos sintéticos, 0 violaciones", { x: 7.1, y: 1.75, w: 5.6, h: 0.4, fontFace: FONT_HEAD, fontSize: 15.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addChart(
      pres.ChartType.bar,
      [
        {
          name: "Casos",
          labels: ["Ofrecer opción\nde pago", "Escalar a\nhumano", "Monitoreo\nsin oferta", "Ofrecer acuerdo\nde pago", "Diferir por\nauto-cura"],
          values: [179, 156, 34, 20, 11],
        },
      ],
      {
        x: 7.0, y: 2.2, w: 5.9, h: 3.85,
        barDir: "bar",
        chartColors: [NAVY],
        showTitle: false,
        showLegend: false,
        showValue: true,
        dataLabelPosition: "outEnd",
        dataLabelColor: NAVY,
        dataLabelFontSize: 11,
        catAxisLabelFontSize: 10.5,
        catAxisLabelColor: TEXT,
        valAxisHidden: true,
        valGridLine: { style: "none" },
        catGridLine: { style: "none" },
        barGapWidthPct: 35,
      }
    );
    s.addText("5 invariantes de negocio verificadas sobre los 400 casos — 0 violaciones en todas.", {
      x: 7.0, y: 6.15, w: 5.9, h: 0.5, fontFace: FONT, fontSize: 11, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });
    pageNum(s, 7);
    s.addNotes("Dirigidas documentan y fijan el comportamiento esperado; masivas dan confianza estadística de que se sostiene a escala, con combinaciones que nadie escribiría a mano.");
  }

  // ===================================================================
  // 8. Producción: arquitectura y caminos
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Del prototipo a la operación: arquitectura y caminos", { size: 25 });

    const flow = ["Feature\nstore", "Entrenamiento\n(MLflow)", "Model\nRegistry", "Scoring\nbatch + on-demand", "Orquestador\nagéntico"];
    const boxW = 2.18, gap = 0.22, startX = 0.6, y = 1.95;
    let lastCx = 0;
    flow.forEach((t, i) => {
      const x = startX + i * (boxW + gap);
      const isLast = i === flow.length - 1;
      s.addShape("roundRect", { x, y, w: boxW, h: 1.2, rectRadius: 0.08, fill: { color: isLast ? ACCENT : NAVY }, line: { type: "none" } });
      s.addText(t, { x: x + 0.08, y, w: boxW - 0.16, h: 1.2, align: "center", valign: "middle", fontFace: FONT, fontSize: 11.5, bold: true, color: WHITE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
      if (!isLast) {
        s.addText("→", { x: x + boxW - 0.02, y: y + 0.38, w: gap + 0.04, h: 0.5, align: "center", fontFace: FONT, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      } else {
        lastCx = x + boxW / 2;
      }
    });

    // Ramificación de caminos desde el orquestador
    const branchY = y + 1.55;
    const hLineY = branchY - 0.25;
    const branches = [
      { t: "Canal cliente", d: "WhatsApp / call center / app" },
      { t: "Cola de escalamiento", d: "Con contexto completo para el gestor" },
      { t: "Observabilidad", d: "Trazas + monitor LLMOps" },
    ];
    const bW = 3.7, bGap = 0.35, bStartX = (W - (bW * 3 + bGap * 2)) / 2;
    const branchCx = branches.map((_, i) => bStartX + i * (bW + bGap) + bW / 2);

    // Línea vertical desde el orquestador hasta la línea horizontal distribuidora
    s.addShape("line", { x: lastCx, y: y + 1.2, w: 0, h: hLineY - (y + 1.2), line: { color: MUTED, width: 1.25 } });
    // Línea horizontal que cubre desde la primera rama hasta el punto de bajada del orquestador
    const hLineLeft = Math.min(branchCx[0], lastCx), hLineRight = Math.max(branchCx[branchCx.length - 1], lastCx);
    s.addShape("line", { x: hLineLeft, y: hLineY, w: hLineRight - hLineLeft, h: 0, line: { color: MUTED, width: 1.25 } });

    branches.forEach((b, i) => {
      const x = bStartX + i * (bW + bGap);
      const cx = branchCx[i];
      s.addShape("line", { x: cx, y: hLineY, w: 0, h: branchY - hLineY, line: { color: MUTED, width: 1.25 } });
      s.addShape("roundRect", { x, y: branchY, w: bW, h: 1.05, rectRadius: 0.08, fill: { color: LIGHTBG }, line: { type: "none" } });
      s.addText(b.t, { x: x + 0.15, y: branchY + 0.1, w: bW - 0.3, h: 0.4, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      s.addText(b.d, { x: x + 0.15, y: branchY + 0.48, w: bW - 0.3, h: 0.5, fontFace: FONT, fontSize: 10.5, italic: true, color: MUTED, isTextBox: true, margin: 0, valign: "top" });
    });

    s.addText("Próximos pasos", { x: 0.6, y: 5.55, w: 5, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const roadmap = [
      "Reemplazar el NLU por reglas con un LLM real + evaluación continua",
      "Conseguir el dato de elegibilidad/producto vigente para el scoring on-demand",
    ];
    roadmap.forEach((r, i) => {
      const y2 = 6.05 + i * 0.55;
      iconCircle(s, ic.checkBlanco, 0.6, y2, 0.38, NAVY);
      s.addText(r, { x: 1.15, y: y2 - 0.03, w: 11.3, h: 0.45, fontFace: FONT, fontSize: 12.5, color: TEXT, isTextBox: true, margin: 0, valign: "middle" });
    });
    pageNum(s, 8);
    s.addNotes("El orquestador reparte en tres caminos paralelos: contacto con el cliente, cola humana, y observabilidad — los tres siempre trazados.");
  }

  // ===================================================================
  // 9. Sistema de monitoreo: métricas y semáforos
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Sistema de monitoreo: qué medimos y cuándo se prende una alerta", { size: 22 });

    function metricRow(x, y, w, color, label, detail) {
      dot(s, x, y + 0.06, 0.16, color);
      s.addText(label, { x: x + 0.32, y: y - 0.08, w: w - 0.32, h: 0.32, fontFace: FONT_HEAD, fontSize: 13, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      s.addText(detail, { x: x + 0.32, y: y + 0.22, w: w - 0.32, h: 0.55, fontFace: FONT, fontSize: 10.3, color: MUTED, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.15 });
    }

    // Columna izquierda: Parte 1
    s.addText("Parte 1 — Modelo", { x: 0.6, y: 1.8, w: 5.9, h: 0.35, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const p1 = [
      { c: GREEN, t: "PSI del score", d: "Estabilidad del score mes a mes. Alerta si > 0.2 (hoy: dic-2023 vs. oot = 0.013)." },
      { c: GREEN, t: "PSI de variables clave", d: "Historial de pagos, mora, demografía. Mismo umbral: > 0.2." },
      { c: ACCENT, t: "SHAP desarrollo vs. producción", d: "Si el modelo empieza a explicar sus decisiones distinto. Revisión mensual." },
      { c: ACCENT, t: "F1 / AUC real vs. predicho", d: "Desempeño real con 1 mes de rezago. Dispara reentrenamiento si cae." },
    ];
    let py = 2.3;
    p1.forEach((m) => { metricRow(0.6, py, 5.9, m.c, m.t, m.d); py += 0.82; });

    // Columna derecha: Parte 2
    s.addText("Parte 2 — Agente", { x: 6.85, y: 1.8, w: 5.9, h: 0.35, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const p2 = [
      { c: GREEN, t: "Ofertas no autorizadas", d: "0% tolerado — bloqueo automático, no solo alerta." },
      { c: ACCENT, t: "Precisión del escalamiento", d: "≥ 85% confirmado como necesario por un gestor humano." },
      { c: ACCENT, t: "Recall de señales sensibles", d: "≥ 95% — el falso negativo es el error costoso aquí." },
    ];
    py = 2.3;
    p2.forEach((m) => { metricRow(6.85, py, 5.9, m.c, m.t, m.d); py += 0.82; });

    // Distribución de caminos (línea base de prueba) — barra apilada
    const barY = py + 0.15;
    s.addText("Distribución de caminos del agente (línea base de prueba, 400 casos sintéticos)", {
      x: 6.85, y: barY, w: 5.9, h: 0.4, fontFace: FONT_HEAD, fontSize: 12, bold: true, color: NAVY, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.1,
    });
    const segs = [
      { l: "Ofrecer opción de pago", pct: 44.75, c: NAVY },
      { l: "Escalar a humano", pct: 39.0, c: ACCENT },
      { l: "Monitoreo sin oferta", pct: 8.5, c: ICE },
      { l: "Acuerdo de pago", pct: 5.0, c: MUTED },
      { l: "Diferir auto-cura", pct: 2.75, c: NAVY_DARK },
    ];
    const barX = 6.85, barW = 5.9, barH = 0.42, barTop = barY + 0.55;
    let sx = barX;
    segs.forEach((sg) => {
      const segW = (barW * sg.pct) / 100;
      s.addShape("rect", { x: sx, y: barTop, w: segW, h: barH, fill: { color: sg.c }, line: { color: WHITE, width: 0.75 } });
      sx += segW;
    });
    // Leyenda en 2 columnas
    let legX = barX, legY = barTop + barH + 0.16;
    segs.forEach((sg, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const lx = barX + col * (barW / 2);
      const ly = legY + row * 0.28;
      s.addShape("rect", { x: lx, y: ly + 0.04, w: 0.14, h: 0.14, fill: { color: sg.c }, line: { type: "none" } });
      s.addText(`${sg.l} (${sg.pct}%)`, { x: lx + 0.2, y: ly - 0.03, w: barW / 2 - 0.2, h: 0.26, fontFace: FONT, fontSize: 9.5, color: MUTED, isTextBox: true, margin: 0 });
    });
    pageNum(s, 9);
    s.addNotes("Verde = ya tenemos referencia validada hoy. Ámbar = métrica definida, línea base a establecer en el piloto. La barra de la derecha es la distribución observada en la prueba masiva, útil como línea base de comparación una vez en producción.");
  }

  // ===================================================================
  // 10. RESUMEN EJECUTIVO
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    title(s, "Resumen ejecutivo", { y: 0.6, h: 0.8 });

    const cardW = 5.95, cardH = 2.05, gap = 0.2;
    const x1 = 0.6, x2 = x1 + cardW + gap;
    const y1 = 1.7, y2 = y1 + cardH + gap;

    // A. El resultado
    s.addShape("roundRect", { x: x1, y: y1, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: LIGHTBG }, line: { type: "none" } });
    s.addText("El resultado", { x: x1 + 0.28, y: y1 + 0.18, w: cardW - 0.56, h: 0.35, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addText("6 de cada 10 clientes marcados como “alta probabilidad de aceptar” efectivamente aceptan — un mes antes de gestionarlos, sin depender solo del monto de la deuda.", {
      x: x1 + 0.28, y: y1 + 0.55, w: cardW - 0.56, h: cardH - 0.7, fontFace: FONT, fontSize: 12.5, color: TEXT, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25,
    });

    // B. Qué automatiza / qué no
    s.addShape("roundRect", { x: x2, y: y1, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Qué automatiza y qué no decide solo", { x: x2 + 0.28, y: y1 + 0.18, w: cardW - 0.56, h: 0.35, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText("Ofrece únicamente lo que la política de crédito ya autorizó. Todo caso sensible, dudoso o fuera de lo normal pasa a un gestor humano, con el contexto completo.", {
      x: x2 + 0.28, y: y1 + 0.55, w: cardW - 0.56, h: cardH - 0.7, fontFace: FONT, fontSize: 12.5, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25,
    });

    // C. Riesgos y controles
    s.addShape("roundRect", { x: x1, y: y2, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: LIGHTBG }, line: { type: "none" } });
    s.addText("Riesgos y sus controles", { x: x1 + 0.28, y: y2 + 0.18, w: cardW - 0.56, h: 0.35, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addText("Modelo desactualizado → monitoreo mensual con alerta. Oferta indebida → bloqueo automático y auditoría del 100%. Riesgo legal/reputacional → humano siempre disponible y trazabilidad completa.", {
      x: x1 + 0.28, y: y2 + 0.55, w: cardW - 0.56, h: cardH - 0.7, fontFace: FONT, fontSize: 11.8, color: TEXT, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.22,
    });

    // D. Alcance de la entrega
    s.addShape("roundRect", { x: x2, y: y2, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("Alcance de esta entrega", { x: x2 + 0.28, y: y2 + 0.18, w: cardW - 0.56, h: 0.35, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText("Prototipo funcional y probado a fondo (49 pruebas, 400 casos sintéticos, cero incidentes de cumplimiento). Sin LLM real ni datos de producción — listo para un piloto controlado.", {
      x: x2 + 0.28, y: y2 + 0.55, w: cardW - 0.56, h: cardH - 0.7, fontFace: FONT, fontSize: 11.8, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.22,
    });

    // Banner de pedido
    const bY = y2 + cardH + 0.25;
    s.addShape("roundRect", { x: 0.6, y: bY, w: cardW * 2 + gap, h: 0.95, rectRadius: 0.1, fill: { color: ACCENT }, line: { type: "none" } });
    s.addText("Pedido: aprobar un piloto controlado — un segmento o mes acotado, con monitoreo diario, antes de escalar a toda la cartera.", {
      x: 0.9, y: bY, w: cardW * 2 + gap - 0.6, h: 0.95, align: "center", valign: "middle", fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY_DARK, isTextBox: true, margin: 0, lineSpacingMultiple: 1.15,
    });
    pageNum(s, 10);
    s.addNotes("Slide para el comité: cerrar aquí, en tono de resultado y control, sin tecnicismos. El pedido es concreto: un piloto, no un despliegue total.");
  }

  const outPath = path.join(__dirname, "..", "Presentacion_Ejecutiva_Prueba_Bancolombia.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Escrito:", outPath);
}

main().catch((e) => { console.error(e); process.exit(1); });
