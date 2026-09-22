"""
Análisis de la muestra OOT puntuada (Parte 1)

`results/resultado_prueba.csv` ES la muestra OOT (Out Of Time): las
112.549 obligaciones de `oot.csv` (enero-2024), ya calificadas por el
modelo final. NO es una simulación ni es el set de validación interno
(train ago-nov / valid dic-2023 dentro de trtest.csv, que sí tiene
respuesta conocida y se usa para medir F1/AUC). Es la entrega real que
pide la prueba.

Nota de nombres: el archivo se sigue llamando `resultado_prueba.csv`
porque así lo exige el nombre y formato de columnas del enunciado; en este
script y en la documentación nos referimos a su contenido como "muestra
OOT puntuada" para dejar claro qué es sin tocar el nombre requerido.

Este script valida que esa entrega no tenga un comportamiento raro:

  1. Sanity checks básicos (nulos, rango de probabilidad, tasa de
     positivos, concentración anómala cerca de 0 o 1).
  2. PSI (Population Stability Index) entre el score de validación
     (dic-2023, respuesta conocida) y el score de la muestra OOT entregada
     (ene-2024) — si la distribución de probabilidades cambiara de forma
     brusca de un mes a otro sin razón de negocio, sería señal de un
     problema (dato mal armado, población distinta, etc.), no solo una
     curiosidad estadística. Cierra el punto que quedó abierto en
     `docs/eda_notas.md` ("no se validó estabilidad poblacional (PSI)
     trtest-vs-oot").
  3. SHAP sobre una muestra de la OOT entregada, comparado contra el
     ranking de importancia ya visto en validación (`notebooks/model_outputs/`)
     — si las variables más influyentes cambiaran de golpe en producción,
     sería señal de deriva de datos, no del modelo en sí.

Salidas en notebooks/oot_outputs/: distribucion_oot_vs_valid.png,
shap_oot.png, resumen_validacion_oot.md.

Ejecutar: python3 notebooks/03_analisis_oot_puntuada.py
Requiere: results/resultado_prueba.csv, results/model_lgbm.txt,
results/feature_cols.json, data/processed/modeling_{trtest,oot}.parquet
(es decir, correr antes src/data_prep.py y src/train.py).
"""
from __future__ import annotations

import json
import os
import sys

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_prep import PROC, TARGET_COL
from train import encode_categoricals
from config import RESULTS_DIR  # noqa: E402 — ver config.py

OUT = os.path.join(os.path.dirname(__file__), "oot_outputs")
os.makedirs(OUT, exist_ok=True)
RESULTS = RESULTS_DIR

COLOR_VALID = "#34608D"
COLOR_OOT = "#B03A2E"


def cargar_todo():
    with open(os.path.join(RESULTS, "feature_cols.json")) as f:
        meta = json.load(f)
    feature_cols, umbral = meta["feature_cols"], meta["threshold"]

    tr = pd.read_parquet(os.path.join(PROC, "modeling_trtest.parquet"))
    oot = pd.read_parquet(os.path.join(PROC, "modeling_oot.parquet"))
    oot_ids = oot["ID"].reset_index(drop=True)

    train_mask = tr["fecha_var_rpta_alt"] < 202312
    valid_mask = tr["fecha_var_rpta_alt"] == 202312
    X_train = tr.loc[train_mask, feature_cols].copy()
    y_train = tr.loc[train_mask, TARGET_COL]
    X_valid = tr.loc[valid_mask, feature_cols].copy()
    y_valid = tr.loc[valid_mask, TARGET_COL]
    X_oot = oot[feature_cols].copy()

    # Alinea categorías EXACTAMENTE como src/train.py (categorías fijadas
    # desde train, nunca desde valid/oot) para reproducir el mismo
    # encoding que produjo resultado_prueba.csv.
    cat_cols = encode_categoricals(X_train, [X_valid, X_oot], feature_cols)

    resultado = pd.read_csv(os.path.join(RESULTS, "resultado_prueba.csv"))
    return X_train, y_train, X_valid, y_valid, X_oot, oot_ids, feature_cols, cat_cols, umbral, resultado


def entrenar_valid_holdout(X_train, y_train, X_valid, y_valid, cat_cols):
    """El mismo modelo/hiperparámetros de src/train.py pero SOLO entrenado
    con ago-nov (el early-stopped, no el reentrenado final con todo
    trtest) -- así el score de referencia para comparar distribuciones es
    un score genuinamente out-of-sample de diciembre, no contaminado por
    haber visto diciembre en el entrenamiento (como sí lo vio el modelo
    final que puntuó la OOT)."""
    dtrain = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_cols, free_raw_data=False)
    dvalid = lgb.Dataset(X_valid, label=y_valid, categorical_feature=cat_cols, reference=dtrain, free_raw_data=False)
    params = dict(
        objective="binary", metric="auc", learning_rate=0.05, num_leaves=63,
        min_data_in_leaf=100, feature_fraction=0.8, bagging_fraction=0.8,
        bagging_freq=1, seed=42, verbose=-1,
    )
    model = lgb.train(
        params, dtrain, num_boost_round=2000, valid_sets=[dvalid],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )
    return model.predict(X_valid, num_iteration=model.best_iteration)


def psi(esperado: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index: compara la distribución de un score
    entre una población de referencia (esperado) y una nueva (actual),
    usando los mismos puntos de corte (deciles de la referencia)."""
    cortes = np.quantile(esperado, np.linspace(0, 1, bins + 1))
    cortes[0], cortes[-1] = -np.inf, np.inf
    cortes = np.unique(cortes)
    pct_e = np.clip(np.histogram(esperado, bins=cortes)[0] / len(esperado), 1e-4, None)
    pct_a = np.clip(np.histogram(actual, bins=cortes)[0] / len(actual), 1e-4, None)
    return float(np.sum((pct_a - pct_e) * np.log(pct_a / pct_e)))


def main():
    X_train, y_train, X_valid, y_valid, X_oot, oot_ids, feature_cols, cat_cols, umbral, resultado = cargar_todo()

    print("=" * 70)
    print("1. SANITY CHECKS DE LA MUESTRA OOT PUNTUADA (resultado_prueba.csv)")
    print("=" * 70)
    n = len(resultado)
    n_nulos = int(resultado.isna().sum().sum())
    print(f"Filas: {n:,} | nulos: {n_nulos} | IDs únicos: {resultado['ID'].nunique():,}")
    print(f"Prob_uno: min={resultado['Prob_uno'].min():.3f}, max={resultado['Prob_uno'].max():.3f}, "
          f"media={resultado['Prob_uno'].mean():.3f}")
    pct_cerca_0 = (resultado["Prob_uno"] < 0.05).mean() * 100
    pct_cerca_1 = (resultado["Prob_uno"] > 0.95).mean() * 100
    print(f"% con score < 0.05: {pct_cerca_0:.1f}% | % con score > 0.95: {pct_cerca_1:.1f}% "
          f"(concentraciones altas aquí serían la señal de alerta)")
    print(f"% predichos positivo (umbral={umbral}): {resultado['var_rpta_alt'].mean() * 100:.1f}%")

    print("\nEntrenando el modelo de referencia ago-nov -> dic-2023 (el mismo "
          "usado para medir F1/AUC en validación) para comparar distribuciones...")
    p_valid = entrenar_valid_holdout(X_train, y_train, X_valid, y_valid, cat_cols)

    valor_psi = psi(p_valid, resultado["Prob_uno"].values)
    interpretacion = (
        "sin cambio poblacional relevante" if valor_psi < 0.1 else
        "cambio moderado, vigilar" if valor_psi < 0.25 else
        "cambio significativo, revisar antes de producción"
    )
    print(f"\nPSI (score dic-2023 [validación] vs. score ene-2024 [OOT entregada]) "
          f"= {valor_psi:.3f} -> {interpretacion}")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    bins = np.linspace(0, 1, 41)
    ax.hist(p_valid, bins=bins, density=True, alpha=0.55, color=COLOR_VALID,
            label="Validación (dic-2023, respuesta conocida)")
    ax.hist(resultado["Prob_uno"], bins=bins, density=True, alpha=0.55, color=COLOR_OOT,
            label="Muestra OOT puntuada (ene-2024, entrega)")
    ax.axvline(umbral, color="black", linestyle="--", linewidth=1, label=f"Umbral de decisión ({umbral})")
    ax.set_xlabel("Probabilidad predicha (Prob_uno)")
    ax.set_ylabel("Densidad")
    ax.set_title(f"Distribución del score: validación vs. OOT entregada (PSI={valor_psi:.3f})")
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "distribucion_oot_vs_valid.png"), dpi=150)
    plt.close()

    print("\n" + "=" * 70)
    print("2. SHAP SOBRE LA MUESTRA OOT: ¿coherente con lo visto en validación?")
    print("=" * 70)
    modelo_final = lgb.Booster(model_file=os.path.join(RESULTS, "model_lgbm.txt"))

    # Sanity extra: las predicciones del modelo final cargado deben
    # reproducir EXACTAMENTE Prob_uno de resultado_prueba.csv (confirma que
    # el archivo entregado sale de este mismo modelo/pipeline, no de otra
    # corrida distinta).
    check = pd.DataFrame({"ID": oot_ids, "check": modelo_final.predict(X_oot)}).merge(resultado, on="ID")
    max_dif = float((check["check"] - check["Prob_uno"]).abs().max())
    print(f"Verificación de reproducibilidad: máxima diferencia entre la predicción "
          f"recalculada aquí y resultado_prueba.csv = {max_dif:.2e} (debe ser ~0)")

    muestra_oot = X_oot.sample(n=min(2000, len(X_oot)), random_state=42)
    explainer = shap.TreeExplainer(modelo_final)
    shap_raw = explainer.shap_values(muestra_oot)
    shap_arr = shap_raw[1] if isinstance(shap_raw, list) else shap_raw

    plt.figure(figsize=(9, 7))
    shap.summary_plot(shap_arr, muestra_oot, max_display=15, show=False)
    plt.title("SHAP sobre la muestra OOT puntuada (enero-2024)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "shap_oot.png"), dpi=150, bbox_inches="tight")
    plt.close()

    imp_oot = pd.Series(np.abs(shap_arr).mean(axis=0), index=feature_cols).sort_values(ascending=False)
    print("\nTop 10 por |SHAP| medio en la muestra OOT:")
    print(imp_oot.head(10).to_string())

    overlap = None
    ruta_importancia_valid = os.path.join(os.path.dirname(__file__), "model_outputs", "feature_importance_detallado.csv")
    if os.path.exists(ruta_importancia_valid):
        top_valid = list(pd.read_csv(ruta_importancia_valid).sort_values("gain", ascending=False).head(10)["feature"])
        top_oot = list(imp_oot.head(10).index)
        overlap = len(set(top_oot) & set(top_valid))
        print(f"\nCoincidencia con el top 10 de importancia (gain) de validación: "
              f"{overlap}/10 variables en común -> "
              f"{'coherente' if overlap >= 7 else 'revisar: baja coincidencia'}")

    with open(os.path.join(OUT, "resumen_validacion_oot.md"), "w") as f:
        f.write("# Validación de la muestra OOT puntuada (resultado_prueba.csv)\n\n")
        f.write(f"- Filas: {n:,}, nulos: {n_nulos}, IDs únicos: {resultado['ID'].nunique():,}\n")
        f.write(f"- Score: min={resultado['Prob_uno'].min():.3f}, max={resultado['Prob_uno'].max():.3f}, "
                f"media={resultado['Prob_uno'].mean():.3f}\n")
        f.write(f"- % score<0.05: {pct_cerca_0:.1f}% | % score>0.95: {pct_cerca_1:.1f}%\n")
        f.write(f"- % predichos positivo (umbral={umbral}): {resultado['var_rpta_alt'].mean() * 100:.1f}%\n")
        f.write(f"- PSI score dic-2023 vs. ene-2024: {valor_psi:.3f} ({interpretacion})\n")
        f.write(f"- Verificación de reproducibilidad del modelo final: diferencia máxima = {max_dif:.2e}\n")
        if overlap is not None:
            f.write(f"- Coincidencia top-10 SHAP (OOT) vs. importancia gain (validación): {overlap}/10\n")

    print(f"\nListo. Salidas en: {OUT}")


if __name__ == "__main__":
    main()
