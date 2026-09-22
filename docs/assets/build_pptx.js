// Genera docs/Presentacion_Ejecutiva_Prueba_Bancolombia.pptx a partir del
// guion en docs/presentacion_ejecutiva.md. Material NO obligatorio de
// entregar (ver nota en ese archivo) -- se construye como cortesía para
// que Jose solo tenga que practicar la sustentación, no diseñar.
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
const FONT = "Calibri";
const FONT_HEAD = "Cambria";

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
  };

  const darkBg = { color: NAVY_DARK };
  const lightBg = { color: WHITE };
  const tintBg = { color: LIGHTBG };

  // -----------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------
  function kicker(slide, text, opts = {}) {
    slide.addText(text.toUpperCase(), {
      x: 0.6, y: opts.y ?? 0.45, w: 8, h: 0.35,
      fontFace: FONT, fontSize: 12, bold: true, charSpacing: 2,
      color: opts.color ?? ACCENT, isTextBox: true, margin: 0,
    });
  }

  function title(slide, text, opts = {}) {
    slide.addText(text, {
      x: 0.6, y: opts.y ?? 0.78, w: opts.w ?? 11.8, h: opts.h ?? 0.9,
      fontFace: FONT_HEAD, fontSize: opts.size ?? 32, bold: true,
      color: opts.color ?? NAVY, isTextBox: true, margin: 0,
    });
  }

  function iconCircle(slide, imgData, x, y, d, bgColor) {
    slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: bgColor }, line: { type: "none" } });
    const pad = d * 0.26;
    slide.addImage({ data: imgData, x: x + pad / 2, y: y + pad / 2, w: d - pad, h: d - pad });
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
    s.addText("Jose Nelson González  ·  Mission SAS", {
      x: 0.9, y: 6.05, w: 8, h: 0.4, fontFace: FONT, fontSize: 14, bold: true,
      color: WHITE, isTextBox: true, margin: 0,
    });
    s.addText("Sustentación técnica y ejecutiva", {
      x: 0.9, y: 6.45, w: 8, h: 0.35, fontFace: FONT, fontSize: 12,
      color: MUTED === NAVY_DARK ? ICE : ICE, isTextBox: true, margin: 0,
    });
    s.addNotes("Portada. Presentarse brevemente y anunciar la estructura: 10 minutos técnicos + 5 minutos para el bloque ejecutivo/no técnico.");
  }

  // ===================================================================
  // 2. AGENDA
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "Agenda · 15 minutos");
    title(s, "Dos bloques, un solo objetivo: decidir");

    const items = [
      { ic: ic.contexto, t: "Contexto y objetivo", d: "1.5 min", sub: "Por qué anticipar la aceptación de opciones de pago" },
      { ic: ic.modelo, t: "Parte 1 — Modelo de propensión", d: "3 min", sub: "Metodología, decisión clave sobre variables y resultado" },
      { ic: ic.agente, t: "Parte 2 — Sistema agéntico", d: "4 min", sub: "Arquitectura, reglas de negocio, pruebas y límites" },
      { ic: ic.produccion, t: "Producción y próximos pasos", d: "1.5 min", sub: "De prototipo a operación monitoreada" },
      { ic: ic.comite, t: "Bloque ejecutivo (no técnico)", d: "5 min", sub: "Impacto de negocio, riesgos y pedido de aprobación" },
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
        x: 1.6, y: y + 0.36, w: 7.9, h: 0.35, fontFace: FONT, fontSize: 11.5, italic: true,
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
    s.addNotes("Recorrer la agenda en 15-20 segundos, sin detenerse en cada punto. Dejar claro que el bloque ejecutivo evita jerga técnica.");
  }

  // ===================================================================
  // 3. CONTEXTO Y OBJETIVO
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "1. Contexto y objetivo · 1.5 min");
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
  // 4. PARTE 1 — Datos y decisión clave sobre variables
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "2. Parte 1 — Modelo de propensión · 3 min");
    title(s, "Datos y la decisión clave sobre variables");

    const cards = [
      { ic: ic.database, t: "4 tablas de origen", d: "≈570K obligaciones-mes, target balanceado" },
      { ic: ic.filtro, t: "Variables contemporáneas excluidas", d: "No están en oot.csv y muestran correlación muy alta con el target del mismo mes" },
      { ic: ic.reloj, t: "Validación temporal, no aleatoria", d: "Separación por tiempo real; umbral optimizado a F1" },
    ];
    const cardW = 3.78, gap = 0.35, startX = 0.6;
    cards.forEach((c, i) => {
      const x = startX + i * (cardW + gap);
      s.addShape("roundRect", { x, y: 2.15, w: cardW, h: 3.55, rectRadius: 0.1, fill: { color: LIGHTBG }, line: { type: "none" } });
      iconCircle(s, c.ic, x + 0.3, 2.45, 0.72, WHITE);
      s.addText(c.t, { x: x + 0.3, y: 3.35, w: cardW - 0.6, h: 0.75, fontFace: FONT_HEAD, fontSize: 15.5, bold: true, color: NAVY, isTextBox: true, margin: 0, lineSpacingMultiple: 1.1 });
      s.addText(c.d, { x: x + 0.3, y: 4.15, w: cardW - 0.6, h: 1.45, fontFace: FONT, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25 });
    });
    s.addText("El pipeline se rediseñó para usar solo variables estrictamente “conocidas antes” del mes a predecir.", {
      x: 0.6, y: 5.95, w: 12.1, h: 0.6, fontFace: FONT, fontSize: 13.5, italic: true, color: NAVY, isTextBox: true, margin: 0,
    });
    pageNum(s, 4);
    s.addNotes("La mayoría de columnas de trtest describen el resultado del mismo mes; por eso no sirven para predecir el mes siguiente sin fuga.");
  }

  // ===================================================================
  // 5. PARTE 1 — Resultado y limitación
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = tintBg;
    kicker(s, "2. Parte 1 — Modelo de propensión · 3 min");
    title(s, "Resultado del modelo y su principal limitación");

    // Stat callouts
    const stats = [
      { v: "0.729", l: "AUC" },
      { v: "0.671", l: "F1 (umbral optimizado)" },
    ];
    stats.forEach((st, i) => {
      const x = 0.6 + i * 3.5;
      s.addShape("roundRect", { x, y: 2.1, w: 3.15, h: 2.05, rectRadius: 0.1, fill: { color: WHITE }, line: { type: "none" } });
      s.addText(st.v, { x, y: 2.28, w: 3.15, h: 1.1, align: "center", fontFace: FONT_HEAD, fontSize: 48, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
      s.addText(st.l, { x, y: 3.4, w: 3.15, h: 0.55, align: "center", fontFace: FONT, fontSize: 13, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    });
    s.addText("Integrando historial de pagos, demografía y scores actuales del banco.", {
      x: 0.6, y: 4.35, w: 6.65, h: 0.7, fontFace: FONT, fontSize: 13, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });

    // Limitation card
    s.addShape("roundRect", { x: 7.55, y: 2.1, w: 5.18, h: 2.95, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
    iconCircle(s, ic.alertaAmbar, 7.85, 2.35, 0.6, NAVY_DARK);
    s.addText("Principal limitación", { x: 8.6, y: 2.42, w: 3.9, h: 0.45, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText(
      "oot.csv no trae elegibilidad ni producto vigente: cerca de la mitad de las obligaciones de enero-2024 son “cold start” y dependen solo de demografía y scores del banco.",
      { x: 7.85, y: 3.05, w: 4.6, h: 1.9, fontFace: FONT, fontSize: 13, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.25 }
    );

    s.addShape("line", { x: 0.6, y: 5.35, w: 12.1, h: 0, line: { color: ICE, width: 1.5 } });
    s.addText("Probar el sistema de punta a punta (no solo cada capa por separado) es lo que reveló esta y otras limitaciones antes de la entrega.", {
      x: 0.6, y: 5.55, w: 12.1, h: 0.6, fontFace: FONT, fontSize: 12.5, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });
    pageNum(s, 5);
    s.addNotes("Enfatizar honestidad metodológica: la limitación de cold-start es real y está documentada, no oculta.");
  }

  // ===================================================================
  // 6. PARTE 2 — Arquitectura del sistema agéntico
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = darkBg;
    kicker(s, "3. Parte 2 — Sistema agéntico · 4 min", { color: ACCENT });
    title(s, "Arquitectura supervisor: lineal y auditable", { color: WHITE });

    const steps = [
      { ic: ic.balanza, t: "Reglas de\nnegocio", sub: "Determinísticas" },
      { ic: ic.cerebro, t: "Siguiente\nMejor Acción", sub: "Usa el score Parte 1" },
      { ic: ic.chat, t: "Conversa-\ncional", sub: "Redacta la oferta" },
      { ic: ic.escudo, t: "Guardrails", sub: "Bloquea lo no autorizado" },
      { ic: ic.persona, t: "Escalamiento", sub: "Gestor humano" },
    ];
    const boxW = 2.05, gap = 0.42, startX = 0.75, y = 2.6;
    steps.forEach((st, i) => {
      const x = startX + i * (boxW + gap);
      s.addShape("roundRect", { x, y, w: boxW, h: 2.5, rectRadius: 0.1, fill: { color: NAVY }, line: { color: ICE, width: 0.75 } });
      iconCircle(s, st.ic, x + boxW / 2 - 0.4, y + 0.28, 0.8, NAVY_DARK);
      s.addText(st.t, { x: x + 0.08, y: y + 1.25, w: boxW - 0.16, h: 0.65, align: "center", fontFace: FONT_HEAD, fontSize: 13, bold: true, color: WHITE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
      s.addText(st.sub, { x: x + 0.08, y: y + 1.92, w: boxW - 0.16, h: 0.5, align: "center", fontFace: FONT, fontSize: 10, italic: true, color: ICE, isTextBox: true, margin: 0 });
      if (i < steps.length - 1) {
        s.addText("→", { x: x + boxW, y: y + 0.85, w: gap, h: 0.6, align: "center", fontFace: FONT, fontSize: 22, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
      }
    });

    s.addText("Por qué separadas del LLM: en cobranza, la oferta debe ser exactamente la autorizada — nunca delegable a que un modelo de lenguaje la “invente”.", {
      x: 0.75, y: 5.55, w: 11.8, h: 0.8, fontFace: FONT, fontSize: 14.5, italic: true, color: ICE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.25,
    });
    pageNum(s, 6);
    s.addNotes("Mostrar el flujo con el dedo/puntero, de izquierda a derecha. Insistir en que las reglas de negocio son la única fuente de verdad sobre qué se puede ofrecer.");
  }

  // ===================================================================
  // 7. PARTE 2 — Pruebas y limitación
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "3. Parte 2 — Sistema agéntico · 4 min");
    title(s, "Probado a fondo, con un límite explícito");

    const stats = [
      { v: "14", l: "escenarios dirigidos", sub: "7 pedidos + robustez + restricción legal" },
      { v: "49", l: "pruebas automatizadas", sub: "42 dirigidas + 7 masivas (400 casos sintéticos)" },
      { v: "0%", l: "tolerancia a ofertas\nno autorizadas", sub: "Cero incidentes de cumplimiento" },
    ];
    const cardW = 3.78, gap = 0.35;
    stats.forEach((st, i) => {
      const x = 0.6 + i * (cardW + gap);
      s.addShape("roundRect", { x, y: 2.15, w: cardW, h: 2.5, rectRadius: 0.1, fill: { color: LIGHTBG }, line: { type: "none" } });
      s.addText(st.v, { x, y: 2.3, w: cardW, h: 1.0, align: "center", fontFace: FONT_HEAD, fontSize: 40, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
      s.addText(st.l, { x: x + 0.2, y: 3.3, w: cardW - 0.4, h: 0.6, align: "center", fontFace: FONT, fontSize: 12.5, bold: true, color: NAVY, isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
      s.addText(st.sub, { x: x + 0.2, y: 3.95, w: cardW - 0.4, h: 0.6, align: "center", fontFace: FONT, fontSize: 10.5, italic: true, color: MUTED, isTextBox: true, margin: 0 });
    });

    s.addShape("roundRect", { x: 0.6, y: 4.95, w: 12.13, h: 1.55, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
    iconCircle(s, ic.alertaAmbar, 0.9, 5.2, 0.62, NAVY_DARK);
    s.addText(
      "Limitación del entorno: sin acceso a un LLM real en esta prueba. El prototipo usa reglas/plantillas, con un punto de extensión explícito para conectar un LLM en producción sin tocar el motor de decisión.",
      { x: 1.75, y: 5.08, w: 10.7, h: 1.3, fontFace: FONT, fontSize: 13, color: WHITE, isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 1.2 }
    );
    pageNum(s, 7);
    s.addNotes("Si preguntan por qué no hay LLM: limitación del entorno de la prueba, no una decisión de diseño definitiva.");
  }

  // ===================================================================
  // 8. Producción y próximos pasos
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "4. Arquitectura de producción · 1.5 min");
    title(s, "Del prototipo a la operación monitoreada");

    const flow = ["Feature store", "Entrenamiento\n(MLflow)", "Scoring batch\n+ on-demand", "Orquestador\nagéntico", "Escalamiento\nhumano", "Monitoreo"];
    const boxW = 1.83, gap = 0.185, startX = 0.6, y = 2.3;
    flow.forEach((t, i) => {
      const x = startX + i * (boxW + gap);
      const isLast = i === flow.length - 1;
      s.addShape("roundRect", { x, y, w: boxW, h: 1.3, rectRadius: 0.08, fill: { color: isLast ? ACCENT : NAVY }, line: { type: "none" } });
      s.addText(t, { x: x + 0.08, y, w: boxW - 0.16, h: 1.3, align: "center", valign: "middle", fontFace: FONT, fontSize: 11, bold: true, color: WHITE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.05 });
      if (!isLast) {
        s.addText("→", { x: x + boxW - 0.02, y: y + 0.42, w: gap + 0.04, h: 0.5, align: "center", fontFace: FONT, fontSize: 16, bold: true, color: NAVY, isTextBox: true, margin: 0 });
      }
    });

    s.addText("Roadmap propuesto", { x: 0.6, y: 4.05, w: 5, h: 0.4, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    const roadmap = [
      "Reemplazar el NLU por reglas con un LLM + evaluación continua",
      "Validar PSI de estabilidad poblacional en producción",
      "Conseguir el dato de elegibilidad vigente para el scoring on-demand",
    ];
    roadmap.forEach((r, i) => {
      const y2 = 4.55 + i * 0.62;
      iconCircle(s, ic.checkBlanco, 0.6, y2, 0.4, NAVY);
      s.addText(r, { x: 1.2, y: y2 - 0.05, w: 11.3, h: 0.5, fontFace: FONT, fontSize: 13, color: TEXT, isTextBox: true, margin: 0, valign: "middle" });
    });
    pageNum(s, 8);
    s.addNotes("Cerrar el bloque técnico. Transición: 'con esto termina la parte técnica; ahora, en términos de negocio...'");
  }

  // ===================================================================
  // 9. DIVISOR — Bloque ejecutivo
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = darkBg;
    s.addShape("ellipse", { x: -2.5, y: 4, w: 6, h: 6, fill: { color: NAVY }, line: { type: "none" } });
    iconCircle(s, ic.comite, W / 2 - 0.55, 1.55, 1.1, NAVY);
    s.addText("BLOQUE EJECUTIVO", { x: 0, y: 3.05, w: W, h: 0.5, align: "center", fontFace: FONT, fontSize: 14, bold: true, charSpacing: 3, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText("Comité directivo no técnico", { x: 0, y: 3.55, w: W, h: 0.9, align: "center", fontFace: FONT_HEAD, fontSize: 34, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText("5 minutos · sin jerga técnica (F1, AUC, LightGBM, LLM) · foco en impacto y riesgo", {
      x: 0, y: 4.5, w: W, h: 0.5, align: "center", fontFace: FONT, fontSize: 14, italic: true, color: ICE, isTextBox: true, margin: 0,
    });
    pageNum(s, 9);
    s.addNotes("Marcar explícitamente el cambio de registro: el objetivo de este bloque es la aprobación de negocio, no explicar la técnica.");
  }

  // ===================================================================
  // 10. El problema y el resultado en términos de negocio
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "Bloque ejecutivo · El problema y el resultado");
    title(s, "“Sabemos, con un mes de anticipación,\nqué clientes van a aceptar”", { size: 26, h: 1.3 });

    s.addShape("roundRect", { x: 0.6, y: 3.75, w: 6.5, h: 2.55, rectRadius: 0.12, fill: { color: NAVY }, line: { type: "none" } });
    s.addText("6", { x: 0.9, y: 3.85, w: 2.3, h: 1.5, fontFace: FONT_HEAD, fontSize: 78, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText("de cada 10", { x: 3.1, y: 4.25, w: 2, h: 0.7, fontFace: FONT, fontSize: 16, bold: true, color: WHITE, isTextBox: true, margin: 0, valign: "middle" });
    s.addText("clientes que el modelo marca como “alta probabilidad de aceptar”, efectivamente aceptan.", {
      x: 0.9, y: 5.35, w: 5.9, h: 0.85, fontFace: FONT, fontSize: 13, color: ICE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.2,
    });

    s.addShape("roundRect", { x: 7.4, y: 3.75, w: 5.33, h: 2.55, rectRadius: 0.12, fill: { color: LIGHTBG }, line: { type: "none" } });
    s.addText("Mejora medible frente a priorizar solo por monto de deuda: se gestiona primero a quien de verdad va a responder, y de forma más personalizada.", {
      x: 7.7, y: 3.95, w: 4.75, h: 2.2, fontFace: FONT, fontSize: 13.5, color: TEXT, isTextBox: true, margin: 0, valign: "middle", lineSpacingMultiple: 1.3,
    });
    pageNum(s, 10);
    s.addNotes("Usar el ejemplo numérico simple (6 de cada 10), no mencionar F1 ni la fórmula. El problema en una frase + el resultado de negocio van juntos en esta slide.");
  }

  // ===================================================================
  // 11. Qué automatiza el asistente y qué NO decide solo
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "Bloque ejecutivo · Alcance del asistente");
    title(s, "Automatiza el contacto, nunca la política de crédito");

    s.addShape("roundRect", { x: 0.6, y: 2.15, w: 5.9, h: 4.35, rectRadius: 0.12, fill: { color: LIGHTBG }, line: { type: "none" } });
    iconCircle(s, ic.check, 0.9, 2.45, 0.7, WHITE);
    s.addText("Sí automatiza", { x: 1.75, y: 2.55, w: 4.5, h: 0.5, fontFace: FONT_HEAD, fontSize: 17, bold: true, color: NAVY, isTextBox: true, margin: 0 });
    s.addText(
      "Ofrecer solo lo que la política de crédito ya autorizó para ese cliente — nunca “inventa” un descuento ni una condición nueva.",
      { x: 0.95, y: 3.35, w: 5.3, h: 2.2, fontFace: FONT, fontSize: 14, color: TEXT, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.3 }
    );

    s.addShape("roundRect", { x: 6.83, y: 2.15, w: 5.9, h: 4.35, rectRadius: 0.12, fill: { color: NAVY }, line: { type: "none" } });
    iconCircle(s, ic.prohibido, 7.13, 2.45, 0.7, NAVY_DARK);
    s.addText("No decide solo", { x: 7.98, y: 2.55, w: 4.5, h: 0.5, fontFace: FONT_HEAD, fontSize: 17, bold: true, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText(
      "Cualquier caso sensible, dudoso o fuera de lo normal se transfiere automáticamente a un gestor humano — con el contexto completo de la conversación.",
      { x: 7.18, y: 3.35, w: 5.2, h: 2.2, fontFace: FONT, fontSize: 14, color: WHITE, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.3 }
    );
    pageNum(s, 11);
    s.addNotes("Aquí mostrar, si el tiempo lo permite, un ejemplo real de transcripción con escalamiento (results/transcripciones_agentico.json) para dar confianza.");
  }

  // ===================================================================
  // 12. Riesgos y cómo se controlan
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = lightBg;
    kicker(s, "Bloque ejecutivo · Gestión de riesgos");
    title(s, "Riesgos y cómo se controlan");

    const risks = [
      { ic: ic.alertaAmbar, t: "El modelo se desactualiza", c: "Monitoreo mensual con alerta automática de deriva" },
      { ic: ic.escudoAmbar, t: "El asistente ofrece algo indebido", c: "Bloqueo automático + auditoría del 100% de las conversaciones" },
      { ic: ic.balanzaAmbar, t: "Riesgo reputacional / legal", c: "Siempre hay un humano disponible y trazabilidad completa de cada decisión" },
    ];
    const cardW = 3.78, gap = 0.35;
    risks.forEach((r, i) => {
      const x = 0.6 + i * (cardW + gap);
      s.addShape("roundRect", { x, y: 2.2, w: cardW, h: 4.15, rectRadius: 0.1, fill: { color: LIGHTBG }, line: { type: "none" } });
      iconCircle(s, r.ic, x + 0.3, 2.5, 0.72, WHITE);
      s.addText(r.t, { x: x + 0.3, y: 3.4, w: cardW - 0.6, h: 0.85, fontFace: FONT_HEAD, fontSize: 14.5, bold: true, color: NAVY, isTextBox: true, margin: 0, lineSpacingMultiple: 1.1 });
      s.addText(r.c, { x: x + 0.3, y: 4.3, w: cardW - 0.6, h: 1.9, fontFace: FONT, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.3 });
    });
    pageNum(s, 12);
    s.addNotes("Cada riesgo con su control: deriva -> monitoreo; oferta indebida -> bloqueo + auditoría; legal/reputacional -> humano + trazabilidad.");
  }

  // ===================================================================
  // 13. Pedido de aprobación (cierre)
  // ===================================================================
  {
    const s = pres.addSlide();
    s.background = darkBg;
    s.addShape("ellipse", { x: 9.8, y: -2.5, w: 6, h: 6, fill: { color: NAVY }, line: { type: "none" } });
    iconCircle(s, ic.apreton, W / 2 - 0.55, 1.15, 1.1, ACCENT);
    s.addText("PEDIDO CONCRETO", { x: 0, y: 2.55, w: W, h: 0.45, align: "center", fontFace: FONT, fontSize: 13, bold: true, charSpacing: 3, color: ACCENT, isTextBox: true, margin: 0 });
    s.addText("Aprobar un piloto controlado", { x: 0, y: 3.0, w: W, h: 0.8, align: "center", fontFace: FONT_HEAD, fontSize: 30, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText(
      "Un segmento o mes acotado, con monitoreo diario, antes de escalar a toda la cartera — definiendo en conjunto con Riesgo, Jurídico y Cumplimiento el umbral de qué se considera un caso “sensible”.",
      { x: W / 2 - 4.6, y: 3.95, w: 9.2, h: 1.6, align: "center", fontFace: FONT, fontSize: 15, color: ICE, isTextBox: true, margin: 0, lineSpacingMultiple: 1.35 }
    );
    s.addShape("line", { x: W / 2 - 1.1, y: 5.9, w: 2.2, h: 0, line: { color: ACCENT, width: 2 } });
    s.addText("Gracias — quedo atento a sus preguntas", { x: 0, y: 6.1, w: W, h: 0.5, align: "center", fontFace: FONT, fontSize: 14, italic: true, color: WHITE, isTextBox: true, margin: 0 });
    pageNum(s, 13);
    s.addNotes("Cierre. Pedido explícito y concreto de aprobación de un piloto, no de un despliegue total.");
  }

  const outPath = path.join(__dirname, "..", "Presentacion_Ejecutiva_Prueba_Bancolombia.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Escrito:", outPath);
}

main().catch((e) => { console.error(e); process.exit(1); });
