"""Entrenamiento del modelo IDS con MLflow tracking.

Se utiliza XGBoost por su rendimiento superior en datasets desbalanceados
de ciberseguridad y su eficiencia en inferencia (< 100ms por predicción).
"""

import logging
import mlflow
import mlflow.sklearn
import pandas as pd
import joblib
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score, f1_score, classification_report,
    precision_score, recall_score, confusion_matrix,
)

from src.models.evaluacion import supera_umbrales

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = Path("src/data/features/cicids_features.csv")
MODEL_PATH = Path("src/models/ids_model.pkl")
MLFLOW_EXPERIMENT = "netshield-ids"
TARGET_COL = "Label"

HIPERPARAMETROS = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "scale_pos_weight": 3.0,
    "eval_metric": "logloss",
    "random_state": 42,
    "n_jobs": -1,
}


def cargar_datos(ruta: Path = DATA_PATH):
    df = pd.read_csv(ruta)
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]
    logger.info("Datos: %d muestras, %d features", X.shape[0], X.shape[1])
    logger.info("Distribución: %s", y.value_counts().to_dict())
    return X, y


def entrenar(X_train, y_train, params: dict):
    modelo = XGBClassifier(**params)
    modelo.fit(X_train, y_train)
    return modelo


def main() -> None:
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    X, y = cargar_datos()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    logger.info("Train: %d | Test: %d", len(X_train), len(X_test))

    with mlflow.start_run(run_name="xgboost-ids-v1"):
        mlflow.log_params(HIPERPARAMETROS)
        mlflow.log_param("n_features", X_train.shape[1])
        mlflow.log_param("n_train_samples", len(X_train))

        modelo = entrenar(X_train, y_train, HIPERPARAMETROS)

        # Evaluar
        y_pred_proba = modelo.predict_proba(X_test)[:, 1]
        y_pred = modelo.predict(X_test)

        auc_roc = roc_auc_score(y_test, y_pred_proba)
        f1_macro = f1_score(y_test, y_pred, average="macro")
        precision_ataque = precision_score(y_test, y_pred, pos_label=1)
        recall_ataque = recall_score(y_test, y_pred, pos_label=1)

        mlflow.log_metric("auc_roc", auc_roc)
        mlflow.log_metric("f1_macro", f1_macro)
        mlflow.log_metric("precision_ataque", precision_ataque)
        mlflow.log_metric("recall_ataque", recall_ataque)

        cv_f1 = cross_val_score(
            XGBClassifier(**HIPERPARAMETROS), X, y, cv=5, scoring="f1_macro",
        ).mean()
        mlflow.log_metric("cv_f1_macro_mean", cv_f1)

        logger.info("AUC-ROC: %.4f | F1-macro: %.4f | Recall ataque: %.4f",
                     auc_roc, f1_macro, recall_ataque)
        logger.info("\n%s", classification_report(
            y_test, y_pred, target_names=["BENIGN", "ATAQUE"],
        ))

        mlflow.sklearn.log_model(modelo, artifact_path="model")
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(modelo, MODEL_PATH)
        mlflow.log_artifact(str(MODEL_PATH))

        # ── QUALITY GATE ─────────────────────────────────────────
        if not supera_umbrales(f1_macro, auc_roc, recall_ataque):
            raise ValueError(
                f"QUALITY GATE FALLIDO — Modelo no supera umbrales.\n"
                f"  F1-macro:      {f1_macro:.3f} (mín: 0.85)\n"
                f"  AUC-ROC:       {auc_roc:.3f} (mín: 0.90)\n"
                f"  Recall ataque: {recall_ataque:.3f} (mín: 0.80)\n"
                f"No se procede al despliegue."
            )

        logger.info("QUALITY GATE SUPERADO — Modelo aprobado para despliegue.")


if __name__ == "__main__":
    main()
