"""
Pipeline de preparación de datos para el modelo de propensión a la
aceptación de opciones de pago.

Principio central (ver docs/eda_notas.md para el detalle): la gran mayoría
de las columnas de `trtest.csv` describen eventos OCURRIDOS DURANTE el mes
de la variable respuesta (gestiones, pagos, acuerdos, alternativa aplicada,
etc.). Usarlas tal cual sería fuga de información, porque son consecuencia
(o coocurrencia directa) de la decisión que se quiere predecir.

Por eso el pipeline reconstruye, para cada combinación obligación-mes, un
"corte" de información conocida ANTES de que empiece el mes de la variable
respuesta (t-1 hacia atrás):

  - Historial propio de la obligación en trtest (mes t-1: mora, saldo,
    gestiones, pagos, si aceptó o no la alternativa anterior).
  - Snapshot demográfico/financiero del cliente (master_customer_data),
    el más reciente disponible con fecha <= t-1.
  - Scores del sistema actual de priorización (probabilidad_oblig_hist)
    en el corte t-1.
  - (si está disponible) Historial de cuotas y pagos
    (maestra_cuotas_pagos_mes_hist) en t-1 y ventana de 3 meses.

Además se conservan como variables contemporáneas SOLO aquellas que
describen la oferta/elegibilidad vigente al inicio del mes (no el
resultado): banca, segmento, producto, cant_alter_posibles y los códigos
de alternativas preaprobadas.
"""
from __future__ import annotations

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (  # noqa: E402 — ver config.py: único lugar donde se editan rutas
    DATA_RAW_DIR, DATA_PROCESSED_DIR, RUTA_TRTEST, RUTA_MASTER_CUSTOMER_DATA,
    RUTA_PROBABILIDAD_OBLIG_HIST, RUTA_MAESTRA_CUOTAS_PAGOS, RUTA_OOT,
)

RAW = DATA_RAW_DIR  # se mantiene por compatibilidad (usado por notebooks/01_eda.py)
PROC = DATA_PROCESSED_DIR
os.makedirs(PROC, exist_ok=True)

ID_COLS = ["nit_enmascarado", "num_oblig_orig_enmascarado", "num_oblig_enmascarado"]

# Columnas de trtest que describen el resultado/consecuencia del mes de la
# variable respuesta (NO usar como feature contemporánea; solo como fuente
# de lags hacia el futuro, es decir, como el "estado pasado" de un mes
# anterior).
LEAKY_OUTCOME_COLS = [
    "cant_gestiones", "cant_gestiones_binario", "rpc", "promesas_cumplidas",
    "cant_promesas_cumplidas_binario", "cant_acuerdo", "cant_acuerdo_binario",
    "descripcion_ranking_mejor_ult", "descripcion_ranking_post_ult",
    "marca_alt_rank", "marca_alt_apli", "valor_cuota_mes", "pago_cuota",
    "porc_pago_cuota", "pago_mes", "porc_pago_mes", "pagos_tanque",
    "marca_debito_mora", "alternativa_aplicada_agr", "marca_agrupada_rgo",
    "marca_pago", "marca_alternativa", "marca_alternativa_orig",
    "min_mora", "max_mora", "dias_mora_fin", "rango_mora",
    "vlr_vencido", "saldo_capital", "endeudamiento",
]

# Columnas contemporáneas seguras: describen la OFERTA vigente al cliente,
# no el resultado de su decisión.
SAFE_CONTEMPORANEOUS_COLS = [
    "banca", "segmento", "producto", "producto_cons", "aplicativo",
    "vlr_obligacion", "cant_alter_posibles",
    "desc_alternativa1", "desc_alternativa2", "desc_alternativa3",
    "alter_posible1_2", "alter_posible2_2", "alter_posible3_2",
]

TARGET_COL = "var_rpta_alt"


def ym_to_idx(s: pd.Series) -> pd.Series:
    """202308 -> 2023*12+8, para poder restar meses fácilmente."""
    s = s.astype(int)
    return (s // 100) * 12 + (s % 100)


def idx_to_ym(idx: int) -> int:
    y, m = divmod(idx, 12)
    if m == 0:
        y -= 1
        m = 12
    return y * 100 + m


def load_base(path: str, has_target: bool) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["ID"] = (
        df["nit_enmascarado"].astype(str)
        + "#" + df["num_oblig_orig_enmascarado"].astype(str)
        + "#" + df["num_oblig_enmascarado"].astype(str)
    )
    df["mes_idx"] = ym_to_idx(df["fecha_var_rpta_alt"])
    return df


def build_own_history_lags(panel: pd.DataFrame, history_source: pd.DataFrame) -> pd.DataFrame:
    """Para cada fila de `panel`, pegar el estado de t-1 (mora, saldo,
    gestiones, pagos, si aceptó la alternativa) de la MISMA obligación
    (num_oblig_enmascarado), leyendo ese estado desde `history_source`
    (siempre trtest, la única tabla que trae esas columnas 'leaky').
    """
    cols_for_lag = [c for c in LEAKY_OUTCOME_COLS if c in history_source.columns] + [TARGET_COL]
    hist = history_source[["num_oblig_enmascarado", "mes_idx"] + cols_for_lag].copy()
    hist = hist.rename(columns={c: f"prev_{c}" for c in cols_for_lag})
    hist["join_idx"] = hist["mes_idx"] + 1  # se pega al mes SIGUIENTE
    hist = hist.drop_duplicates(subset=["num_oblig_enmascarado", "join_idx"])
    hist = hist.drop(columns=["mes_idx"])
    out = panel.merge(
        hist, left_on=["num_oblig_enmascarado", "mes_idx"],
        right_on=["num_oblig_enmascarado", "join_idx"], how="left",
    ).drop(columns=["join_idx"])
    return out


def join_master_customer(panel: pd.DataFrame, mc_path: str) -> pd.DataFrame:
    mc = pd.read_csv(mc_path)
    mc["mes_idx"] = mc["year"] * 12 + mc["month"]
    keep_cols = [c for c in mc.columns if c not in ("year", "month", "ingestion_day")]
    mc = mc[keep_cols].drop_duplicates(subset=["nit_enmascarado", "mes_idx"])
    # merge_asof con `by` exige que la columna `on` esté ordenada de forma
    # GLOBAL (no solo dentro de cada grupo).
    mc = mc.sort_values("mes_idx").rename(columns={"mes_idx": "mc_mes_idx"})

    panel = panel.copy()
    panel["cutoff_idx"] = panel["mes_idx"] - 1  # solo info <= t-1
    panel_sorted = panel.sort_values("cutoff_idx").reset_index(drop=True)

    # merge_asof vectorizado agrupando por cliente (mucho más rápido que un
    # loop en Python; internamente hace el join grupo a grupo en C).
    out = pd.merge_asof(
        panel_sorted, mc,
        left_on="cutoff_idx", right_on="mc_mes_idx",
        by="nit_enmascarado", direction="backward",
    )
    # Flag explícito: el panel demográfico es disperso (no todos los
    # clientes tienen snapshot todos los meses); esta bandera separa
    # "no hay dato porque el cliente nunca aparece en el panel" de
    # "no hay dato porque el snapshot más cercano es posterior al corte".
    out["tiene_snapshot_demografico"] = out["mc_mes_idx"].notna().astype("int8")
    return out


def join_prob_oblig(panel: pd.DataFrame, prob_path: str) -> pd.DataFrame:
    prob = pd.read_csv(prob_path)
    prob = prob.drop_duplicates(subset=["num_oblig_enmascarado", "fecha_corte"])
    prob["mes_idx"] = ym_to_idx(prob["fecha_corte"])
    prob["join_idx"] = prob["mes_idx"] + 1  # se usa en el mes SIGUIENTE (t-1 -> t)
    prob = prob.rename(columns={
        "prob_propension": "prob_propension_prev",
        "prob_alrt_temprana": "prob_alrt_temprana_prev",
        "prob_auto_cura": "prob_auto_cura_prev",
        "lote": "lote_prev",
    })[["num_oblig_enmascarado", "join_idx", "prob_propension_prev",
        "prob_alrt_temprana_prev", "prob_auto_cura_prev", "lote_prev"]]

    out = panel.merge(
        prob, left_on=["num_oblig_enmascarado", "mes_idx"],
        right_on=["num_oblig_enmascarado", "join_idx"], how="left",
    ).drop(columns=["join_idx"])
    return out


def join_cuotas_pagos(panel: pd.DataFrame, cuotas_path: str) -> pd.DataFrame:
    """Historial de cuotas/pagos: lag t-1 + agregados de ventana 3 meses.
    Se activa solo si el archivo está disponible."""
    if not os.path.exists(cuotas_path):
        return panel
    usecols = ["nit_enmascarado", "num_oblig_enmascarado", "fecha_corte",
               "valor_cuota_mes", "pago_total", "porc_pago", "marca_pago",
               "ajustes_banco"]
    cu = pd.read_csv(cuotas_path, usecols=usecols)
    # OJO: en esta tabla fecha_corte viene como YYYYMMDD (fin de mes), no
    # YYYYMM como en las otras tablas -> se normaliza con //100.
    cu["fecha_corte"] = (cu["fecha_corte"] // 100).astype(int)
    cu["mes_idx"] = ym_to_idx(cu["fecha_corte"])
    # porc_pago trae divisiones por cuota=0 -> inf; se limpia y se capa a un
    # rango razonable (pagos muy por encima de la cuota sí son válidos,
    # pero inf/valores absurdos son artefactos de la división).
    cu["porc_pago"] = cu["porc_pago"].replace([np.inf, -np.inf], np.nan)
    cu.loc[cu["porc_pago"] > 1000, "porc_pago"] = np.nan
    cu = cu.drop_duplicates(subset=["num_oblig_enmascarado", "mes_idx"])
    cu = cu.sort_values(["num_oblig_enmascarado", "mes_idx"])

    # lag t-1 directo
    lag1 = cu.copy()
    lag1["join_idx"] = lag1["mes_idx"] + 1
    lag1 = lag1.rename(columns={
        "valor_cuota_mes": "cuota_prev", "pago_total": "pago_total_prev",
        "porc_pago": "porc_pago_prev", "marca_pago": "marca_pago_prev",
        "ajustes_banco": "ajuste_banco_prev",
    })[["num_oblig_enmascarado", "join_idx", "cuota_prev", "pago_total_prev",
        "porc_pago_prev", "marca_pago_prev", "ajuste_banco_prev"]]

    panel = panel.merge(
        lag1, left_on=["num_oblig_enmascarado", "mes_idx"],
        right_on=["num_oblig_enmascarado", "join_idx"], how="left",
    ).drop(columns=["join_idx"])

    # agregados de ventana 3 meses (t-1, t-2, t-3), vectorizado: un merge
    # por cada lag y luego promedio/conteo por fila (evita apply row-wise).
    porc = cu[["num_oblig_enmascarado", "mes_idx", "porc_pago"]]
    lag_cols = []
    for k in (1, 2, 3):
        lk = porc.copy()
        lk["join_idx"] = lk["mes_idx"] + k
        lk = lk.rename(columns={"porc_pago": f"_porc_pago_lag{k}"})[
            ["num_oblig_enmascarado", "join_idx", f"_porc_pago_lag{k}"]
        ]
        panel = panel.merge(
            lk, left_on=["num_oblig_enmascarado", "mes_idx"],
            right_on=["num_oblig_enmascarado", "join_idx"], how="left",
        ).drop(columns=["join_idx"])
        lag_cols.append(f"_porc_pago_lag{k}")

    panel["porc_pago_mean_3m"] = panel[lag_cols].mean(axis=1, skipna=True)
    panel["porc_pago_meses_con_dato_3m"] = panel[lag_cols].notna().sum(axis=1)
    panel = panel.drop(columns=lag_cols)
    return panel


def build_dataset(which: str) -> pd.DataFrame:
    """which: 'trtest' o 'oot'."""
    tr_full = load_base(RUTA_TRTEST, has_target=True)
    if which == "trtest":
        panel = tr_full
    else:
        panel = load_base(RUTA_OOT, has_target=False)

    panel = build_own_history_lags(panel, history_source=tr_full)
    panel = join_master_customer(panel, RUTA_MASTER_CUSTOMER_DATA)
    panel = join_prob_oblig(panel, RUTA_PROBABILIDAD_OBLIG_HIST)
    panel = join_cuotas_pagos(panel, RUTA_MAESTRA_CUOTAS_PAGOS)
    return panel


if __name__ == "__main__":
    tr = build_dataset("trtest")
    tr.to_parquet(os.path.join(PROC, "modeling_trtest.parquet"), index=False)
    print("trtest features:", tr.shape)

    oot = build_dataset("oot")
    oot.to_parquet(os.path.join(PROC, "modeling_oot.parquet"), index=False)
    print("oot features:", oot.shape)
