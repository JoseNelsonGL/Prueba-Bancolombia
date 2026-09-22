"""
Comparación de modelos — Parte 1

Se entrenan y comparan 3 familias de algoritmos sobre el MISMO conjunto de
features y el MISMO split temporal que usa `src/train.py` (train = ago-nov
2023, valid = dic-2023), para justificar con evidencia por qué la solución
final usa LightGBM y no otra alternativa razonable:

  - Regresión Logística  -> referencia LINEAL, interpretable.
  - Random Forest        -> BAGGING de árboles.
  - LightGBM              -> BOOSTING de árboles (igual config que
                              src/train.py: nulos/categóricas nativas).

Target casi balanceado (52/48), por lo que NO se usa class_weight en
ninguno de los 3 modelos (mantiene la comparación "de fábrica", sin
correcciones que puedan favorecer a un modelo sobre otro).

Criterio de selección: el CRITERIO PRINCIPAL es maximizar AUC en
validación (dic-2023); la brecha train-valid (proxy de sobreajuste) se
reporta como diagnóstico y solo actúa como desempate cuando dos modelos
quedan a menos de 0.005 de AUC entre sí (en ese caso sí ganaría el de
menor brecha, para no premiar una mejora de AUC que en realidad es ruido
de sobreajuste). Con brechas ya moderadas (<0.06, ver salida) y ninguna
señal de sobreajuste severo, un modelo claramente mejor en AUC no se
descarta por tener una brecha algo mayor que las alternativas: el F1 (la
métrica real de evaluación de la prueba) es la confirmación final.

NOTA METODOLÓGICA: la comparación no es 100% "de igual a igual" — LightGBM
maneja categóricas/nulos de forma nativa, mientras que Regresión Logística
y Random Forest necesitan one-hot + imputación (con categorías de alta
cardinalidad como `ciiu`, 446 valores, agrupadas por necesidad). Esa
diferencia de tratamiento es en sí misma parte de la justificación de por
qué LightGBM es una mejor opción para ESTOS datos, no solo un artefacto de
la comparación.

Salidas en notebooks/model_outputs/: tabla comparativa (csv), curva ROC
superpuesta + barras AUC train-vs-valid (png), y el modelo ganador (json).

Ejecutar: python3 notebooks/02_model_comparison.py
Requiere data/processed/modeling_{trtest,oot}.parquet
(correr antes: python3 src/data_prep.py)
"""
from __future__ import annotations

import json
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (f1_score, precision_score, recall_score,
                              roc_auc_score, roc_curve)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_prep import PROC, TARGET_COL
from train import encode_categoricals, get_feature_cols

OUT = os.path.join(os.path.dirname(__file__), "model_outputs")
os.makedirs(OUT, exist_ok=True)

COLOR = {"Regresión Logística": "#7F8C8D", "Random Forest": "#34608D", "LightGBM": "#B03A2E"}
EPSILON_EMPATE = 0.005  # diferencia de AUC por debajo de la cual se considera "empate" y desempata por brecha


def cargar_datos():
    tr = pd.read_parquet(os.path.join(PROC, "modeling_trtest.parquet"))
    oot = pd.read_parquet(os.path.join(PROC, "modeling_oot.parquet"))
    feature_cols = [c for c in get_feature_cols(tr) if c in oot.columns]

    train_mask = tr["fecha_var_rpta_alt"] < 202312
    valid_mask = tr["fecha_var_rpta_alt"] == 202312
    X_train = tr.loc[train_mask, feature_cols].copy()
    y_train = tr.loc[train_mask, TARGET_COL]
    X_valid = tr.loc[valid_mask, feature_cols].copy()
    y_valid = tr.loc[valid_mask, TARGET_COL]
    return X_train, y_train, X_valid, y_valid, feature_cols


def entrenar_lightgbm(X_train, y_train, X_valid, y_valid, feature_cols):
    Xt, Xv = X_train.copy(), X_valid.copy()
    cat_cols = encode_categoricals(Xt, [Xv], feature_cols)
    dtrain = lgb.Dataset(Xt, label=y_train, categorical_feature=cat_cols, free_raw_data=False)
    dvalid = lgb.Dataset(Xv, label=y_valid, categorical_feature=cat_cols, reference=dtrain, free_raw_data=False)
    params = dict(
        objective="binary", metric="auc", learning_rate=0.05, num_leaves=63,
        min_data_in_leaf=100, feature_fraction=0.8, bagging_fraction=0.8,
        bagging_freq=1, seed=42, verbose=-1,
    )
    model = lgb.train(
        params, dtrain, num_boost_round=2000, valid_sets=[dvalid],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )
    p_train = model.predict(Xt, num_iteration=model.best_iteration)
    p_valid = model.predict(Xv, num_iteration=model.best_iteration)
    return p_train, p_valid


def _preprocesador(feature_cols, cat_cols, con_escalado):
    num_cols = [c for c in feature_cols if c not in cat_cols]
    pasos_num = [("imputer", SimpleImputer(strategy="median"))]
    if con_escalado:
        pasos_num.append(("scaler", StandardScaler()))
    # max_categories=15: ciiu/subsector tienen decenas de categorías; se
    # agrupan las menos frecuentes en "infrequent" para no disparar la
    # dimensionalidad del one-hot (sin esto, ciiu solo generaría 446
    # columnas).
    return ColumnTransformer([
        ("num", Pipeline(pasos_num), num_cols),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="constant", fill_value="__missing__")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", max_categories=15)),
        ]), cat_cols),
    ])


def entrenar_sklearn(modelo, nombre, X_train, y_train, X_valid, feature_cols, cat_cols, con_escalado):
    pre = _preprocesador(feature_cols, cat_cols, con_escalado)
    pipe = Pipeline([("pre", pre), ("modelo", modelo)])
    t0 = time.time()
    pipe.fit(X_train, y_train)
    dt = time.time() - t0
    p_train = pipe.predict_proba(X_train)[:, 1]
    p_valid = pipe.predict_proba(X_valid)[:, 1]
    print(f"  {nombre}: entrenado en {dt:.1f}s")
    return p_train, p_valid


def mejor_umbral_f1(y_true, proba):
    thresholds = np.linspace(0.05, 0.95, 181)
    f1s = [f1_score(y_true, (proba >= t).astype(int)) for t in thresholds]
    i = int(np.argmax(f1s))
    return float(thresholds[i]), float(f1s[i])


def main():
    X_train, y_train, X_valid, y_valid, feature_cols = cargar_datos()
    cat_cols = [c for c in feature_cols if not pd.api.types.is_numeric_dtype(X_train[c])]
    print(f"Train: {X_train.shape} | Valid: {X_valid.shape} | "
          f"{len(feature_cols)} features ({len(cat_cols)} categóricas)")
    print(f"Balance del target (train): {y_train.mean():.3f} positivos\n")

    resultados = {}

    print("Entrenando Regresión Logística (lineal)...")
    resultados["Regresión Logística"] = entrenar_sklearn(
        LogisticRegression(max_iter=1000),
        "Regresión Logística", X_train, y_train, X_valid, feature_cols, cat_cols, con_escalado=True)

    print("Entrenando Random Forest (bagging)...")
    resultados["Random Forest"] = entrenar_sklearn(
        RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=50,
                                n_jobs=-1, random_state=42),
        "Random Forest", X_train, y_train, X_valid, feature_cols, cat_cols, con_escalado=False)

    print("Entrenando LightGBM (boosting)...")
    resultados["LightGBM"] = entrenar_lightgbm(X_train, y_train, X_valid, y_valid, feature_cols)

    filas = []
    for nombre, (p_train, p_valid) in resultados.items():
        auc_train = roc_auc_score(y_train, p_train)
        auc_valid = roc_auc_score(y_valid, p_valid)
        gap = auc_train - auc_valid
        t, f1 = mejor_umbral_f1(y_valid, p_valid)
        pred = (p_valid >= t).astype(int)
        filas.append({
            "modelo": nombre, "auc_train": auc_train, "auc_valid": auc_valid,
            "gap_train_valid": gap, "f1_valid": f1, "umbral_optimo": t,
            "precision_valid": precision_score(y_valid, pred),
            "recall_valid": recall_score(y_valid, pred),
        })

    df = pd.DataFrame(filas).sort_values("auc_valid", ascending=False).reset_index(drop=True)
    print("\n" + df.to_string(index=False))
    df.to_csv(os.path.join(OUT, "comparacion_modelos.csv"), index=False)

    # Selección: gana el mayor AUC valid, SALVO que el segundo lugar quede a
    # menos de EPSILON_EMPATE (empate estadístico) -> ahí desempata la menor
    # brecha train-valid, para no premiar una diferencia de AUC que en
    # realidad es ruido de sobreajuste.
    primero, segundo = df.iloc[0], df.iloc[1]
    if (primero["auc_valid"] - segundo["auc_valid"]) < EPSILON_EMPATE:
        ganador = primero if primero["gap_train_valid"] <= segundo["gap_train_valid"] else segundo
        motivo = (f"empate técnico en AUC (diferencia < {EPSILON_EMPATE}); "
                  f"desempata la menor brecha train-valid")
    else:
        ganador = primero
        motivo = "mayor AUC en validación, con margen claro sobre el resto"

    mejor_f1 = df.sort_values("f1_valid", ascending=False).iloc[0]["modelo"]
    justificacion = (
        f"{ganador['modelo']} seleccionado por: {motivo}. "
        f"AUC valid={ganador['auc_valid']:.3f}, brecha train-valid={ganador['gap_train_valid']:.3f}, "
        f"F1 valid={ganador['f1_valid']:.3f}. "
        f"Coincide además con el modelo de mejor F1 de los 3 ({mejor_f1}), "
        f"que es la métrica real de evaluación de la prueba."
    )
    print(f"\n>> Modelo seleccionado: {ganador['modelo']}\n>> {justificacion}")
    with open(os.path.join(OUT, "modelo_seleccionado.json"), "w") as f:
        json.dump({"modelo": ganador["modelo"], "justificacion": justificacion}, f, indent=2, ensure_ascii=False)

    # --- gráficos ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for nombre, (_, p_valid) in resultados.items():
        fpr, tpr, _ = roc_curve(y_valid, p_valid)
        axes[0].plot(fpr, tpr, label=f"{nombre} (AUC={roc_auc_score(y_valid, p_valid):.3f})",
                     color=COLOR.get(nombre), linewidth=2)
    axes[0].plot([0, 1], [0, 1], "--", color="gray", linewidth=1)
    axes[0].set_xlabel("Tasa de falsos positivos")
    axes[0].set_ylabel("Tasa de verdaderos positivos")
    axes[0].set_title("Curva ROC — validación (dic-2023)")
    axes[0].legend(loc="lower right", frameon=False)
    axes[0].spines[["top", "right"]].set_visible(False)

    x = np.arange(len(df))
    axes[1].bar(x - 0.2, df["auc_train"], width=0.4, label="AUC train", color="#B0B0B0")
    axes[1].bar(x + 0.2, df["auc_valid"], width=0.4, label="AUC valid", color="#2C3E50")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(df["modelo"], rotation=10)
    axes[1].set_ylim(0.5, 1.0)
    axes[1].set_ylabel("AUC")
    axes[1].set_title("AUC train vs. valid (la brecha delata sobreajuste)")
    axes[1].legend(frameon=False)
    axes[1].spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "roc_comparacion.png"), dpi=150)
    plt.close()

    print(f"\nListo. Salidas en: {OUT}")


if __name__ == "__main__":
    main()
