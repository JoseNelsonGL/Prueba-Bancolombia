"""
Entrenamiento del modelo de propensión a aceptación de opciones de pago.

Validación: esquema TEMPORAL, no aleatorio. Se entrena con los primeros
meses de trtest y se valida con el último mes disponible (dic-2023), que es
la aproximación más fiel al escenario real: el modelo debe predecir un mes
que aún no ha ocurrido (igual que se le pedirá para enero-2024 / oot).

Se optimiza el umbral de decisión para maximizar F1 en el set de
validación (la métrica de la prueba), en lugar de usar 0.5 por defecto.
"""
from __future__ import annotations

import json
import os

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from data_prep import LEAKY_OUTCOME_COLS, PROC, TARGET_COL

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(MODEL_DIR, exist_ok=True)

ID_LIKE = {
    "nit_enmascarado", "num_oblig_orig_enmascarado", "num_oblig_enmascarado",
    "ID", "fecha_var_rpta_alt", "mes_idx", "cutoff_idx", "mc_mes_idx",
    "tipo_var_rpta_alt", TARGET_COL,
}
# columnas contemporáneas del propio trtest que SÍ son seguras (oferta
# vigente, no resultado)
KEEP_RAW = {
    "banca", "segmento", "producto", "producto_cons", "aplicativo",
    "vlr_obligacion", "cant_alter_posibles",
    "desc_alternativa1", "desc_alternativa2", "desc_alternativa3",
    "alter_posible1_2", "alter_posible2_2", "alter_posible3_2",
}


def get_feature_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if c in ID_LIKE:
            continue
        if c in LEAKY_OUTCOME_COLS and c not in KEEP_RAW:
            continue  # versión "cruda" del mismo mes -> fuga; se usa prev_*
        cols.append(c)
    return cols


def encode_categoricals(train: pd.DataFrame, others: list[pd.DataFrame], feature_cols: list[str]):
    """Codifica categóricas como 'category' de pandas con las MISMAS
    categorías vistas en train (categoría nueva en oot -> NaN), para que
    LightGBM las maneje nativamente."""
    cat_cols = [c for c in feature_cols if not pd.api.types.is_numeric_dtype(train[c])]
    for c in cat_cols:
        cats = train[c].astype("category").cat.categories
        train[c] = pd.Categorical(train[c], categories=cats)
        for o in others:
            if c in o.columns:
                o[c] = pd.Categorical(o[c], categories=cats)
    return cat_cols


def main():
    tr = pd.read_parquet(os.path.join(PROC, "modeling_trtest.parquet"))
    oot = pd.read_parquet(os.path.join(PROC, "modeling_oot.parquet"))

    feature_cols = get_feature_cols(tr)
    feature_cols = [c for c in feature_cols if c in oot.columns]  # solo comunes

    # split temporal: train = ago-nov 2023, valid = dic 2023
    train_mask = tr["fecha_var_rpta_alt"] < 202312
    valid_mask = tr["fecha_var_rpta_alt"] == 202312

    X_train, y_train = tr.loc[train_mask, feature_cols].copy(), tr.loc[train_mask, TARGET_COL]
    X_valid, y_valid = tr.loc[valid_mask, feature_cols].copy(), tr.loc[valid_mask, TARGET_COL]
    X_oot = oot[feature_cols].copy()

    cat_cols = encode_categoricals(X_train, [X_valid, X_oot], feature_cols)

    dtrain = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_cols, free_raw_data=False)
    dvalid = lgb.Dataset(X_valid, label=y_valid, categorical_feature=cat_cols, reference=dtrain, free_raw_data=False)

    params = dict(
        objective="binary",
        metric="auc",
        learning_rate=0.05,
        num_leaves=63,
        min_data_in_leaf=100,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=1,
        seed=42,
        verbose=-1,
    )
    model = lgb.train(
        params, dtrain, num_boost_round=2000,
        valid_sets=[dtrain, dvalid], valid_names=["train", "valid"],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )

    proba_valid = model.predict(X_valid, num_iteration=model.best_iteration)
    auc = roc_auc_score(y_valid, proba_valid)

    # búsqueda de umbral óptimo para F1
    thresholds = np.linspace(0.05, 0.95, 181)
    f1s = [f1_score(y_valid, (proba_valid >= t).astype(int)) for t in thresholds]
    best_idx = int(np.argmax(f1s))
    best_t, best_f1 = thresholds[best_idx], f1s[best_idx]
    pred_best = (proba_valid >= best_t).astype(int)

    metrics = {
        "auc_valid_dic2023": float(auc),
        "best_threshold": float(best_t),
        "f1_valid_dic2023": float(best_f1),
        "precision_valid": float(precision_score(y_valid, pred_best)),
        "recall_valid": float(recall_score(y_valid, pred_best)),
        "n_train": int(len(X_train)),
        "n_valid": int(len(X_valid)),
        "n_features": len(feature_cols),
        "best_iteration": int(model.best_iteration),
    }
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    imp = pd.DataFrame({
        "feature": feature_cols,
        "gain": model.feature_importance(importance_type="gain"),
    }).sort_values("gain", ascending=False)
    print("\nTop 20 variables por importancia (gain):")
    print(imp.head(20).to_string(index=False))

    # reentrenar con TODO trtest (train+valid) para el modelo final de producción
    X_full = tr[feature_cols].copy()
    for c in cat_cols:
        X_full[c] = pd.Categorical(X_full[c], categories=X_train[c].cat.categories)
    y_full = tr[TARGET_COL]
    dfull = lgb.Dataset(X_full, label=y_full, categorical_feature=cat_cols, free_raw_data=False)
    final_model = lgb.train(params, dfull, num_boost_round=model.best_iteration)

    final_model.save_model(os.path.join(MODEL_DIR, "model_lgbm.txt"))
    imp.to_csv(os.path.join(MODEL_DIR, "feature_importance.csv"), index=False)
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    with open(os.path.join(MODEL_DIR, "feature_cols.json"), "w") as f:
        json.dump({"feature_cols": feature_cols, "cat_cols": cat_cols, "threshold": best_t}, f, indent=2, ensure_ascii=False)

    # scoring OOT con el modelo final
    proba_oot = final_model.predict(X_oot)
    pred_oot = (proba_oot >= best_t).astype(int)
    out = pd.DataFrame({
        "ID": oot["ID"].values,
        "var_rpta_alt": pred_oot,
        "Prob_uno": proba_oot,
    })
    out.to_csv(os.path.join(MODEL_DIR, "resultado_prueba.csv"), index=False)
    print(f"\nresultado_prueba.csv generado: {out.shape}, tasa positivos={out['var_rpta_alt'].mean():.3f}")


if __name__ == "__main__":
    main()
