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
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6))
ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
ax.axis("off")

box(ax, 0.3, 4.6, 2.2, 1.0, "Cliente\n(proactivo / reactivo)")
box(ax, 3.0, 4.6, 2.3, 1.0, "Agente de\nContexto")
box(ax, 5.7, 4.6, 2.5, 1.0, "Modelo Parte 1\n(score de propensión)", color=COLOR_BOX_ALT)

box(ax, 3.0, 3.1, 2.3, 1.0, "Reglas de negocio\n(elegibilidad,\ndeterminístico)")
box(ax, 5.7, 3.1, 2.5, 1.0, "Siguiente Mejor\nAcción (NBA)")

box(ax, 3.0, 1.6, 2.3, 1.0, "Agente\nConversacional")
box(ax, 5.7, 1.6, 2.5, 1.0, "Guardrails\n(seguridad)")

box(ax, 8.6, 3.1, 2.1, 1.0, "Escalamiento\na gestor humano", color="#B03A2E")
box(ax, 8.6, 1.6, 2.1, 1.0, "Trazabilidad\n(logs JSON)", color=COLOR_BOX_ALT)

arrow(ax, 2.5, 5.1, 3.0, 5.1)
arrow(ax, 4.15, 4.6, 4.15, 4.1)
arrow(ax, 5.3, 3.6, 5.7, 3.6)
arrow(ax, 6.95, 4.6, 6.95, 4.1)
arrow(ax, 4.15, 3.1, 4.15, 2.6)
arrow(ax, 5.3, 2.1, 5.7, 2.1)
arrow(ax, 6.95, 3.1, 6.95, 2.6)
arrow(ax, 8.2, 3.6, 8.6, 3.6)
arrow(ax, 8.2, 2.1, 8.6, 2.1)

ax.text(5.5, 5.75, "Parte 2 — Orquestador del sistema agéntico (patrón supervisor lineal)",
        ha="center", fontsize=12, fontweight="bold", color=COLOR_BOX)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "diagrama_arquitectura_parte2.png"), dpi=170, facecolor="white")
plt.close()

print("Diagramas generados en", OUT)
