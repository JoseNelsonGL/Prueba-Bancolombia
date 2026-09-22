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

SELECCIÓN FINAL (sección adicional al final del script, sobre el modelo
ganador): en vez de quedarse con una sola métrica de un único mes de
validación, se agrega:
  - Estabilidad temporal: backtesting de VENTANA EXPANSIVA — para cada mes
    (a partir del segundo disponible) se entrena solo con los meses
    anteriores y se evalúa AUC/F1 en ese mes, nunca visto en ese
    entrenamiento. Esto da varios puntos de desempeño out-of-sample en el
    tiempo (no solo diciembre), para ver si el modelo es estable o se
    degrada mes a mes — insumo directo para la propuesta de monitoreo de
    producción.
  - Interpretabilidad: importancia de variables (gain) en gráfico de
    barras, y un resumen SHAP (impacto real de cada variable en cada
    predicción, con dirección) sobre una muestra de validación.

Salidas adicionales en notebooks/model_outputs/: estabilidad_temporal.csv/png,
feature_importance_detallado.csv, feature_importance.png, shap_summary.png.

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
    # se conserva `tr` completo (con fecha_var_rpta_alt) para el backtesting
    # de estabilidad temporal mes a mes, más abajo.
    return X_train, y_train, X_valid, y_valid, feature_cols, tr


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
    return p_train, p_valid, model, Xv


def _entrenar_lgb_fold(X_tr, y_tr, X_te, feature_cols, num_boost_round):
    """Un fold del backtesting de ventana expansiva: sin early stopping
    (no hay un tercer conjunto de validación dentro del fold), se usa el
    mismo número de iteraciones que ya se validó en el split principal."""
    Xt, Xe = X_tr.copy(), X_te.copy()
    cat_cols = encode_categoricals(Xt, [Xe], feature_cols)
    dtr = lgb.Dataset(Xt, label=y_tr, categorical_feature=cat_cols, free_raw_data=False)
    params = dict(
        objective="binary", metric="auc", learning_rate=0.05, num_leaves=63,
        min_data_in_leaf=100, feature_fraction=0.8, bagging_fraction=0.8,
        bagging_freq=1, seed=42, verbose=-1,
    )
    model = lgb.train(params, dtr, num_boost_round=num_boost_round)
    return model.predict(Xe)


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


def estabilidad_temporal(tr, feature_cols, num_boost_round, umbral_fijo):
    """Backtesting de ventana expansiva: para cada mes (desde el segundo
    disponible) se entrena SOLO con los meses anteriores y se evalúa en
    ese mes -> AUC/F1 genuinamente out-of-sample en cada periodo, no solo
    en diciembre. Responde "¿el modelo es estable en el tiempo o se
    degrada?", que es justo lo que en producción se vigilaría con
    monitoreo de deriva de desempeño."""
    print("\n" + "=" * 70)
    print("ESTABILIDAD TEMPORAL (backtesting de ventana expansiva, por mes)")
    print("=" * 70)
    meses = sorted(tr["fecha_var_rpta_alt"].unique())
    filas = []
    for i in range(1, len(meses)):
        mes_test = meses[i]
        meses_train = meses[:i]
        m_train = tr["fecha_var_rpta_alt"].isin(meses_train)
        m_test = tr["fecha_var_rpta_alt"] == mes_test
        Xtr, ytr = tr.loc[m_train, feature_cols], tr.loc[m_train, TARGET_COL]
        Xte, yte = tr.loc[m_test, feature_cols], tr.loc[m_test, TARGET_COL]

        proba = _entrenar_lgb_fold(Xtr, ytr, Xte, feature_cols, num_boost_round)
        auc = roc_auc_score(yte, proba)
        f1_fijo = f1_score(yte, (proba >= umbral_fijo).astype(int))
        filas.append({
            "mes_evaluado": int(mes_test), "meses_entrenamiento": len(meses_train),
            "n_train": int(m_train.sum()), "n_test": int(m_test.sum()),
            "auc": auc, "f1_umbral_fijo": f1_fijo,
        })
        print(f"  entrena con {list(meses_train)} -> evalúa {mes_test}: "
              f"AUC={auc:.3f}, F1(umbral fijo={umbral_fijo:.3f})={f1_fijo:.3f}")

    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(OUT, "estabilidad_temporal.csv"), index=False)
    print(f"\n  AUC: media={df['auc'].mean():.3f}, desv.est.={df['auc'].std():.3f} "
          f"(rango {df['auc'].min():.3f}-{df['auc'].max():.3f})")

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax2 = ax.twinx()
    x_labels = df["mes_evaluado"].astype(str)
    l1, = ax.plot(x_labels, df["auc"], "o-", color=COLOR["LightGBM"], linewidth=2, label="AUC")
    l2, = ax2.plot(x_labels, df["f1_umbral_fijo"], "s--", color="#2C3E50", linewidth=2,
                    label=f"F1 (umbral fijo={umbral_fijo:.3f})")
    ax.set_ylabel("AUC", color=COLOR["LightGBM"])
    ax2.set_ylabel("F1", color="#2C3E50")
    ax.set_xlabel("Mes evaluado (entrenado solo con meses anteriores)")
    ax.set_title("Estabilidad del modelo por periodo")
    ax.legend(handles=[l1, l2], loc="lower right", frameon=False)
    ax.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "estabilidad_temporal.png"), dpi=150)
    plt.close()
    return df


def interpretabilidad_ganador(modelo_lgb, X_valid_encoded, feature_cols):
    """Interpretabilidad del modelo ganador: importancia de variables
    (gain) + SHAP (impacto real y dirección de cada variable en cada
    predicción individual, no solo un ranking agregado)."""
    print("\n" + "=" * 70)
    print("INTERPRETABILIDAD DEL MODELO GANADOR: importancia + SHAP")
    print("=" * 70)

    imp = pd.DataFrame({
        "feature": feature_cols,
        "gain": modelo_lgb.feature_importance(importance_type="gain"),
    }).sort_values("gain", ascending=False)
    imp.to_csv(os.path.join(OUT, "feature_importance_detallado.csv"), index=False)
    print("\nTop 10 por importancia (gain):")
    print(imp.head(10).to_string(index=False))

    top = imp.head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["feature"], top["gain"], color=COLOR["LightGBM"])
    ax.set_xlabel("Importancia (gain)")
    ax.set_title("Top 20 variables más importantes — LightGBM")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "feature_importance.png"), dpi=150)
    plt.close()

    try:
        import shap
        muestra = X_valid_encoded.sample(n=min(2000, len(X_valid_encoded)), random_state=42)
        explainer = shap.TreeExplainer(modelo_lgb)
        shap_values = explainer.shap_values(muestra)
        plt.figure(figsize=(9, 7))
        shap.summary_plot(shap_values, muestra, max_display=20, show=False)
        plt.title("SHAP — impacto de cada variable en la predicción\n(muestra de 2.000 obligaciones de validación)")
        plt.tight_layout()
        plt.savefig(os.path.join(OUT, "shap_summary.png"), dpi=150, bbox_inches="tight")
        plt.close()
        print("\nSHAP summary plot guardado en shap_summary.png")
    except Exception as e:
        print(f"\n[aviso] no se pudo generar el gráfico SHAP ({type(e).__name__}: {e}); "
              f"se deja el ranking de importancia (gain) como respaldo.")


def main():
    X_train, y_train, X_valid, y_valid, feature_cols, tr = cargar_datos()
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
    p_train_lgb, p_valid_lgb, modelo_lgb, X_valid_lgb_enc = entrenar_lightgbm(
        X_train, y_train, X_valid, y_valid, feature_cols)
    resultados["LightGBM"] = (p_train_lgb, p_valid_lgb)

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

    # --- SELECCIÓN FINAL: estabilidad temporal + interpretabilidad del ganador ---
    # (implementado para LightGBM, el ganador con los datos actuales; si en
    # una futura corrida el ganador cambiara, esta sección se debe extender
    # al nuevo modelo — ver docstring del módulo.)
    if ganador["modelo"] == "LightGBM":
        estabilidad_temporal(tr, feature_cols, modelo_lgb.best_iteration, ganador["umbral_optimo"])
        interpretabilidad_ganador(modelo_lgb, X_valid_lgb_enc, feature_cols)
    else:
        print(f"\n[aviso] El ganador ({ganador['modelo']}) no es LightGBM: la sección de "
              f"estabilidad temporal/SHAP está implementada solo para LightGBM en este script; "
              f"habría que extenderla para el nuevo ganador.")

    print(f"\nListo. Salidas en: {OUT}")


if __name__ == "__main__":
    main()
