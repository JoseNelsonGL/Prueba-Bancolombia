"""Genera los diagramas de arquitectura (PNG) para el documento metodológico."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = os.path.dirname(__file__)

COLOR_BOX = "#2C3E50"
COLOR_BOX_ALT = "#34608D"
COLOR_TEXT = "white"
COLOR_ARROW = "#7F8C8D"


def box(ax, x, y, w, h, text, color=COLOR_BOX, fontsize=9.5):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                        linewidth=0, facecolor=color)
    ax.add_patch(b)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=COLOR_TEXT, fontsize=fontsize, fontweight="bold", wrap=True)


def arrow(ax, x1, y1, x2, y2):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                         color=COLOR_ARROW, linewidth=1.6)
    ax.add_patch(a)


# ---------------------------------------------------------------------------
# Diagrama 1: pipeline de datos y modelo (Parte 1)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.set_xlim(0, 11)
ax.set_ylim(0, 5.5)
ax.axis("off")

box(ax, 0.3, 4.0, 2.3, 1.0, "trtest.csv\n(ago-dic 2023)")
box(ax, 0.3, 2.7, 2.3, 1.0, "master_customer_data\n(panel jul-dic 2023)")
box(ax, 0.3, 1.4, 2.3, 1.0, "probabilidad_oblig_hist\n(scores del banco)")
box(ax, 0.3, 0.1, 2.3, 1.0, "maestra_cuotas_pagos\n(historial de pagos)")

box(ax, 3.4, 2.05, 2.6, 1.9, "Pipeline de features\n(data_prep.py)\n\nSolo información\nt-1 hacia atrás\n(sin fuga)", color=COLOR_BOX_ALT)

box(ax, 6.7, 3.0, 2.0, 1.0, "Entrenamiento\nLightGBM\n(split temporal)")
box(ax, 6.7, 1.0, 2.0, 1.0, "Scoring OOT\n(enero 2024)")

box(ax, 9.2, 3.0, 1.5, 1.0, "MLflow\n(tracking +\nregistry)")
box(ax, 9.2, 1.0, 1.5, 1.0, "resultado_\nprueba.csv")

for y in (4.5, 3.2, 1.9, 0.6):
    arrow(ax, 2.6, y, 3.4, 3.0)

arrow(ax, 6.0, 3.0, 6.7, 3.5)
arrow(ax, 6.0, 3.0, 6.7, 1.5)
arrow(ax, 8.7, 3.5, 9.2, 3.5)
arrow(ax, 8.7, 1.5, 9.2, 1.5)
arrow(ax, 7.7, 3.0, 7.7, 2.0)

ax.text(5.5, 5.2, "Parte 1 — Modelo de propensión a aceptación de opciones de pago",
        ha="center", fontsize=12, fontweight="bold", color=COLOR_BOX)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "diagrama_pipeline_parte1.png"), dpi=170, facecolor="white")
plt.close()

# ---------------------------------------------------------------------------
# Diagrama 2: arquitectura del sistema agéntico (Parte 2)
# Deliberadamente NO es un flujo de cajitas genérico: se dibuja por CAPAS
# (núcleo determinístico vs. capa conversacional vs. seguridad vs.
# trazabilidad) para que la separación que defiende el documento --
# "qué se ofrece" nunca delegado a lenguaje natural -- se vea, no solo se
# lea.
# ---------------------------------------------------------------------------
COLOR_CORE = "#1F3B57"       # núcleo determinístico (mismo tono que Parte 1, pero...
COLOR_CORE_BG = "#DCE6EF"    # ...con una zona propia detrás, para diferenciarlo
COLOR_CONVO = "#2E86AB"      # capa conversacional (reemplazable por LLM)
COLOR_SECURITY = "#B9770E"   # guardrails: color de "atención", no de flujo normal
COLOR_ESCALA = "#B03A2E"
COLOR_TRAZA = "#5D6D7E"

fig, ax = plt.subplots(figsize=(11, 6.6))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6.6)
ax.axis("off")

ax.text(5.5, 6.3, "Parte 2 — Sistema agéntico: separación por capas, no un flujo genérico",
        ha="center", fontsize=12.5, fontweight="bold", color=COLOR_BOX)

# --- Capa 0: entrada ---
box(ax, 0.3, 5.1, 2.1, 0.75, "Cliente\n(proactivo / reactivo)", color=COLOR_TRAZA, fontsize=9)
box(ax, 0.3, 4.15, 2.1, 0.75, "Modelo Parte 1\n(score de propensión)", color=COLOR_TRAZA, fontsize=9)
arrow(ax, 2.4, 5.475, 2.9, 5.0)
arrow(ax, 2.4, 4.525, 2.9, 4.75)

# --- Zona 1: NÚCLEO DETERMINÍSTICO (reglas + NBA), con fondo propio ---
core_bg = FancyBboxPatch((2.9, 3.65), 3.5, 2.3, boxstyle="round,pad=0.03,rounding_size=0.12",
                          linewidth=1.6, edgecolor=COLOR_CORE, facecolor=COLOR_CORE_BG)
ax.add_patch(core_bg)
ax.text(4.65, 5.72, "NÚCLEO DETERMINÍSTICO — nunca delegado a lenguaje natural",
        ha="center", fontsize=8.3, fontweight="bold", color=COLOR_CORE, style="italic")
box(ax, 3.1, 4.7, 3.1, 0.75, "Elegibilidad (reglas de negocio)\nqué se PUEDE ofrecer", color=COLOR_CORE, fontsize=8.7)
box(ax, 3.1, 3.8, 3.1, 0.75, "Siguiente Mejor Acción (NBA)\ncuál priorizar", color=COLOR_CORE, fontsize=8.7)
arrow(ax, 4.65, 4.7, 4.65, 4.55)

# --- Zona 2: CAPA CONVERSACIONAL (reemplazable por LLM) ---
convo_bg = FancyBboxPatch((6.75, 4.15), 2.4, 1.75, boxstyle="round,pad=0.03,rounding_size=0.12",
                           linewidth=1.6, edgecolor=COLOR_CONVO, facecolor="#DDEEF6")
ax.add_patch(convo_bg)
ax.text(7.95, 5.72, "CAPA CONVERSACIONAL\n(punto de extensión → LLM real)",
        ha="center", fontsize=8.3, fontweight="bold", color=COLOR_CONVO, style="italic")
box(ax, 6.9, 4.35, 2.1, 1.15, "Agente Conversacional\n(redacta, interpreta\nintención)", color=COLOR_CONVO, fontsize=8.7)
arrow(ax, 6.2, 4.4, 6.9, 4.85)

# --- Zona 3: SEGURIDAD (banda horizontal que envuelve la interacción) ---
sec_bg = FancyBboxPatch((2.9, 2.55), 6.25, 0.85, boxstyle="round,pad=0.02,rounding_size=0.08",
                         linewidth=1.4, edgecolor=COLOR_SECURITY, facecolor="#FBEEDC", linestyle="--")
ax.add_patch(sec_bg)
ax.text(6.02, 2.975, "GUARDRAILS — defensa en profundidad: manipulación, señales sensibles, info. contradictoria,\nvalida que NINGUNA respuesta mencione una alternativa no autorizada",
        ha="center", va="center", fontsize=6.3, fontweight="bold", color="#7E4E10")
arrow(ax, 4.65, 3.8, 4.65, 3.4)
arrow(ax, 7.95, 4.15, 6.5, 3.4)

# --- Escalamiento ---
box(ax, 8.65, 2.6, 2.05, 0.85, "Escalamiento a\ngestor humano\n(con contexto completo)", color=COLOR_ESCALA, fontsize=8.3)
arrow(ax, 9.15, 2.55, 9.15, 2.05)
arrow(ax, 9.7, 2.55, 9.7, 2.05)

# --- Trazabilidad: banda inferior que subyace a TODO el flujo ---
traza_bg = FancyBboxPatch((0.3, 0.35), 10.4, 0.85, boxstyle="round,pad=0.02,rounding_size=0.06",
                           linewidth=1.2, edgecolor=COLOR_TRAZA, facecolor="#EAECEE", linestyle=":")
ax.add_patch(traza_bg)
ax.text(5.5, 0.775, "TRAZABILIDAD — cada decisión de cada agente, con session_id, timestamp y motivo (capa transversal, no un paso más del flujo)",
        ha="center", va="center", fontsize=8.2, fontweight="bold", color="#34495E")
for x in (1.5, 4.65, 7.95, 9.7):
    arrow(ax, x, 2.55 if x != 9.7 else 2.55, x, 1.2)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "diagrama_arquitectura_parte2.png"), dpi=170, facecolor="white")
plt.close()

print("Diagramas generados en", OUT)
