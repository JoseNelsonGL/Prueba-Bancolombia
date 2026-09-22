"""
EDA reproducible — Parte 1 (modelo de propensión a aceptación de opciones de pago)

Objetivo de este script: dejar en código, no solo en texto, la evidencia que
sustenta los hallazgos de `docs/eda_notas.md`. Concretamente:

  1. Qué variables trae cada una de las 5 tablas crudas (para que cualquiera
     pueda ver el punto de partida sin abrir los CSV).
  2. Evidencia empírica de por qué algunas columnas de trtest.csv no se usan
     en su versión del mismo mes: no están disponibles en oot.csv y,
     además, su correlación con el target (var_rpta_alt) es mucho más alta
     en versión CONTEMPORÁNEA (tal como vienen, mismo mes) que en su
     versión REZAGADA a t-1 (la que realmente entra al modelo). La caída de
     correlación es consistente con que esas columnas describen el
     resultado, no con que sean un predictor legítimo.
  3. Cómo se va depurando/enriqueciendo el conjunto de variables a medida
     que avanza el pipeline (columnas descartadas por disponibilidad/
     consistencia temporal, columnas agregadas por cada cruce), ejecutando
     las MISMAS funciones de
     `src/data_prep.py` paso a paso (no una narración aparte: si el pipeline
     cambia, este script refleja el cambio real).
  4. Calidad de datos: nulos del panel demográfico y valores inválidos de
     edad_cli.

Salidas (PNG + markdown) en notebooks/eda_outputs/.
Ejecutar desde la raíz del repo: python3 notebooks/01_eda.py
Requiere las 5 tablas en data/raw/ (ver README.md).
"""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_prep import (  # reutiliza la lógica real del pipeline de producción
    RAW, TARGET_COL, LEAKY_OUTCOME_COLS, SAFE_CONTEMPORANEOUS_COLS,
    load_base, build_own_history_lags, join_master_customer, join_prob_oblig,
    join_cuotas_pagos,
)

OUT = os.path.join(os.path.dirname(__file__), "eda_outputs")
os.makedirs(OUT, exist_ok=True)

COLOR_MAIN = "#2C3E50"
COLOR_ALT = "#34608D"
COLOR_LEAK = "#B03A2E"
COLOR_OK = "#1E8449"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white"})


# ---------------------------------------------------------------------------
# 1. Resumen de las 5 tablas crudas: shape + variables
# ---------------------------------------------------------------------------
def resumen_tablas() -> None:
    specs = [
        ("trtest.csv", "nit_enmascarado"),
        ("master_customer_data.csv", "nit_enmascarado"),
        ("probabilidad_oblig_hist.csv", "num_oblig_enmascarado"),
        ("maestra_cuotas_pagos_mes_hist.csv", "num_oblig_enmascarado"),
        ("oot.csv", "nit_enmascarado"),
        ("sample_submission.csv", "ID"),
    ]
    lines = ["# Resumen de tablas crudas (data/raw/)\n"]
    print("=" * 70, "\n1. RESUMEN DE TABLAS CRUDAS\n", "=" * 70, sep="")
    for fname, first_col in specs:
        path = os.path.join(RAW, fname)
        header = pd.read_csv(path, nrows=0)
        n_rows = len(pd.read_csv(path, usecols=[first_col]))
        bloque = (
            f"\n## {fname}\n"
            f"- Filas: {n_rows:,} | Columnas: {header.shape[1]}\n"
            f"- Variables: {', '.join(header.columns)}\n"
        )
        lines.append(bloque)
        print(f"\n{fname} -> {n_rows:,} filas x {header.shape[1]} columnas")
        print(f"  variables: {list(header.columns)}")
    with open(os.path.join(OUT, "00_resumen_tablas.md"), "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# 2. Evidencia de disponibilidad/consistencia temporal: correlación contemporánea vs. t-1
# ---------------------------------------------------------------------------
def _corr_con_target(serie: pd.Series, target: pd.Series) -> float:
    s = serie
    if not pd.api.types.is_numeric_dtype(s):
        s = pd.Series(pd.factorize(s.astype(str))[0], index=s.index)
    mask = s.notna() & target.notna()
    if mask.sum() < 30:
        return np.nan
    return float(np.corrcoef(s[mask], target[mask])[0, 1])


def correlacion_fuga(tr_full: pd.DataFrame, tr_lag: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("2. VARIABLES NO DISPONIBLES EN OOT: CORRELACIÓN CON EL TARGET (contemporánea vs t-1)")
    print("=" * 70)
    candidatas = [
        "marca_pago", "porc_pago_mes", "marca_alternativa", "cant_acuerdo",
        "dias_mora_fin", "saldo_capital", "cant_gestiones", "rpc",
        "valor_cuota_mes", "vlr_vencido", "pago_mes",
    ]
    candidatas = [c for c in candidatas if c in tr_full.columns]

    filas = []
    for c in candidatas:
        corr_contemp = _corr_con_target(tr_full[c], tr_full[TARGET_COL])
        prev_col = f"prev_{c}"
        corr_prev = (
            _corr_con_target(tr_lag[prev_col], tr_lag[TARGET_COL])
            if prev_col in tr_lag.columns else np.nan
        )
        filas.append({"variable": c, "corr_contemporanea": corr_contemp, "corr_t_menos_1": corr_prev})
        print(f"  {c:<22} corr contemporánea = {corr_contemp:+.3f}   |   corr t-1 (prev_{c}) = {corr_prev:+.3f}")

    df = pd.DataFrame(filas).sort_values("corr_contemporanea", key=abs, ascending=True)
    df.to_csv(os.path.join(OUT, "01_correlacion_fuga.csv"), index=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(df))
    ax.barh(y - 0.2, df["corr_contemporanea"].abs(), height=0.4, color=COLOR_LEAK, label="Contemporánea (mismo mes) — no disponible en oot")
    ax.barh(y + 0.2, df["corr_t_menos_1"].abs(), height=0.4, color=COLOR_OK, label="Rezagada a t-1 — usada en el modelo")
    ax.set_yticks(y)
    ax.set_yticklabels(df["variable"])
    ax.set_xlabel("|correlación| con var_rpta_alt")
    ax.set_title("La correlación artificial desaparece al usar información de t-1")
    ax.legend(loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "01_correlacion_fuga.png"), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# 3. Embudo de variables: cómo evoluciona el conjunto de columnas
# ---------------------------------------------------------------------------
def embudo_variables(tr_full: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("3. EVOLUCIÓN DEL CONJUNTO DE VARIABLES A LO LARGO DEL PIPELINE")
    print("=" * 70)
    etapas = []

    raw_cols = [c for c in tr_full.columns if c not in ("ID", "mes_idx")]
    etapas.append(("0. trtest.csv crudo", len(raw_cols)))

    id_like = {"nit_enmascarado", "num_oblig_orig_enmascarado", "num_oblig_enmascarado",
               "fecha_var_rpta_alt", TARGET_COL}
    leaky_a_descartar = [c for c in LEAKY_OUTCOME_COLS if c in raw_cols and c not in SAFE_CONTEMPORANEOUS_COLS]
    seguras = [c for c in raw_cols if c not in id_like and c not in leaky_a_descartar]
    etapas.append(("1. tras excluir IDs y columnas contemporáneas no disponibles en oot", len(seguras)))

    tr_lag = build_own_history_lags(tr_full, history_source=tr_full)
    nuevas = [c for c in tr_lag.columns if c not in tr_full.columns]
    etapas.append(("2. + historial propio rezagado (prev_*)", len(seguras) + len(nuevas)))

    tr_mc = join_master_customer(tr_lag, os.path.join(RAW, "master_customer_data.csv"))
    nuevas_mc = [c for c in tr_mc.columns if c not in tr_lag.columns]
    etapas.append(("3. + snapshot demográfico (master_customer_data)", etapas[-1][1] + len(nuevas_mc)))

    tr_prob = join_prob_oblig(tr_mc, os.path.join(RAW, "probabilidad_oblig_hist.csv"))
    nuevas_prob = [c for c in tr_prob.columns if c not in tr_mc.columns]
    etapas.append(("4. + scores del banco (probabilidad_oblig_hist)", etapas[-1][1] + len(nuevas_prob)))

    tr_cu = join_cuotas_pagos(tr_prob, os.path.join(RAW, "maestra_cuotas_pagos_mes_hist.csv"))
    nuevas_cu = [c for c in tr_cu.columns if c not in tr_prob.columns]
    etapas.append(("5. + historial de cuotas/pagos (maestra_cuotas_pagos_mes_hist)", etapas[-1][1] + len(nuevas_cu)))

    # conjunto final realmente usado por src/train.py (get_feature_cols),
    # intersectado con las columnas disponibles en oot (solo lo común se
    # puede usar para predecir enero-2024).
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from train import get_feature_cols
    oot_cols = pd.read_parquet(
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", "modeling_oot.parquet")
    ).columns if os.path.exists(
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", "modeling_oot.parquet")
    ) else tr_cu.columns
    finales = [c for c in get_feature_cols(tr_cu) if c in oot_cols]
    etapas.append(("6. features finales usadas por el modelo (∩ con oot.csv)", len(finales)))

    for nombre, n in etapas:
        print(f"  {nombre}: {n} columnas")

    df = pd.DataFrame(etapas, columns=["etapa", "n_columnas"])
    df.to_csv(os.path.join(OUT, "02_embudo_variables.csv"), index=False)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = [COLOR_LEAK, COLOR_ALT, COLOR_ALT, COLOR_ALT, COLOR_ALT, COLOR_OK]
    ax.barh(range(len(df)), df["n_columnas"], color=colors)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["etapa"])
    ax.invert_yaxis()
    for i, v in enumerate(df["n_columnas"]):
        ax.text(v + 1, i, str(v), va="center", fontsize=9)
    ax.set_xlabel("Número de columnas")
    ax.set_title("Cómo evoluciona el conjunto de variables a lo largo del pipeline")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "02_embudo_variables.png"), dpi=150)
    plt.close()
    return tr_cu


# ---------------------------------------------------------------------------
# 4. Calidad de datos: nulos demográficos + edad_cli inválida
# ---------------------------------------------------------------------------
def calidad_datos() -> None:
    print("\n" + "=" * 70)
    print("4. CALIDAD DE DATOS: PANEL DEMOGRÁFICO")
    print("=" * 70)
    mc = pd.read_csv(os.path.join(RAW, "master_customer_data.csv"))

    nulos = (mc.isna().mean() * 100).round(1).sort_values(ascending=False)
    nulos = nulos[nulos > 0].head(12)
    print("\nTop columnas con más nulos (%):")
    print(nulos.to_string())

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].barh(range(len(nulos)), nulos.values, color=COLOR_ALT)
    axes[0].set_yticks(range(len(nulos)))
    axes[0].set_yticklabels(nulos.index)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("% nulos")
    axes[0].set_title("Nulos por columna — master_customer_data.csv")
    axes[0].spines[["top", "right"]].set_visible(False)

    if "edad_cli" in mc.columns:
        edad = mc["edad_cli"].dropna()
        n_invalida = int(((edad <= 0) | (edad > 100)).sum())
        print(f"\nedad_cli: min={edad.min()}, max={edad.max()}, "
              f"valores fuera de [1,100] = {n_invalida} ({n_invalida/len(edad)*100:.2f}%)")
        axes[1].hist(edad, bins=60, color=COLOR_ALT, edgecolor="white")
        axes[1].axvspan(edad.min(), 1, color=COLOR_LEAK, alpha=0.3, label="Inválido (≤0)")
        axes[1].axvspan(100, edad.max(), color=COLOR_LEAK, alpha=0.3, label="Inválido (>100)")
        axes[1].set_title(f"edad_cli: {n_invalida} valores inválidos ({n_invalida/len(edad)*100:.1f}%)")
        axes[1].set_xlabel("edad_cli")
        axes[1].legend(frameon=False)
        axes[1].spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "03_calidad_datos_demograficos.png"), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    resumen_tablas()

    tr_full = load_base(os.path.join(RAW, "trtest.csv"), has_target=True)
    tr_lag = build_own_history_lags(tr_full, history_source=tr_full)
    correlacion_fuga(tr_full, tr_lag)
    embudo_variables(tr_full)
    calidad_datos()

    print("\n" + "=" * 70)
    print(f"Listo. Salidas en: {OUT}")
    print("=" * 70)
