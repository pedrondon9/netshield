"""Feature engineering: escalado robusto de las features seleccionadas.

Se aplica RobustScaler en lugar de StandardScaler porque el tráfico
malicioso genera outliers extremos (ej: DDoS con miles de paquetes/segundo)
que sesgarían la media y desviación estándar.
"""

import logging
import joblib
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import RobustScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_PATH = Path("src/data/processed/cicids_processed.csv")
OUTPUT_PATH = Path("src/data/features/cicids_features.csv")
SCALER_PATH = Path("src/models/scaler.pkl")
TARGET_COL = "Label"


def escalar_features(df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
    """Aplica RobustScaler a las features numéricas (no al target)."""
    df = df.copy()
    feature_cols = [c for c in df.columns if c != TARGET_COL]

    if fit:
        scaler = RobustScaler()
        df[feature_cols] = scaler.fit_transform(df[feature_cols])
        SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scaler, SCALER_PATH)
        logger.info("Scaler ajustado y guardado en %s", SCALER_PATH)
    else:
        scaler = joblib.load(SCALER_PATH)
        df[feature_cols] = scaler.transform(df[feature_cols])
        logger.info("Scaler cargado desde %s", SCALER_PATH)

    return df


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    df_feat = escalar_features(df, fit=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_feat.to_csv(OUTPUT_PATH, index=False)
    logger.info("Features escaladas guardadas en %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
