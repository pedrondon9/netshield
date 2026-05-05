"""Limpieza y transformaciones del dataset CICIDS2017.

Problemas conocidos del dataset que se resuelven aquí:
1. Valores infinitos en 'Flow Bytes/s' y 'Flow Packets/s' (división por cero
   cuando Flow Duration = 0)
2. Valores negativos en columnas de duración y longitud
3. Filas duplicadas (~15% del dataset)
4. NaN dispersos tras conversión de tipos
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INPUT_PATH = Path("src/data/validated/cicids_validated.csv")
OUTPUT_PATH = Path("src/data/processed/cicids_processed.csv")

# Columnas duplicadas o irrelevantes
COLS_TO_DROP = ["Fwd Header Length.1"]

# Las 14 features más discriminantes para detección de intrusiones,
# seleccionadas por importancia (RF) + conocimiento de dominio en ciberseguridad
SELECTED_FEATURES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Flow IAT Mean",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "SYN Flag Count",
    "ACK Flag Count",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
]

TARGET_COL = "Label"


def limpiar_infinitos(df: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza valores infinitos por NaN (se imputarán después).

    CICIDS2017 genera infinitos en columnas de tasa (bytes/s, packets/s)
    cuando Flow Duration es cero.
    """
    df = df.copy()
    cols_num = df.select_dtypes(include=[np.number]).columns
    n_inf = np.isinf(df[cols_num]).sum().sum()
    if n_inf > 0:
        logger.info("Reemplazando %d valores infinitos por NaN", n_inf)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


def limpiar_negativos(df: pd.DataFrame) -> pd.DataFrame:
    """Corrige valores negativos en columnas que deben ser >= 0."""
    df = df.copy()
    cols_no_negativas = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if any(kw in c.lower() for kw in [
            "length", "duration", "packets", "bytes", "size", "count"
        ])
    ]
    for col in cols_no_negativas:
        n_neg = (df[col] < 0).sum()
        if n_neg > 0:
            logger.info("Corrigiendo %d negativos en '%s'", n_neg, col)
            df.loc[df[col] < 0, col] = 0
    return df


def imputar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Imputa NaN con la mediana de cada columna numérica."""
    df = df.copy()
    cols_num = df.select_dtypes(include=[np.number]).columns
    n_nulos = df[cols_num].isna().sum().sum()
    if n_nulos > 0:
        logger.info("Imputando %d NaN con mediana por columna", n_nulos)
        for col in cols_num:
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())
    return df


def eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas duplicadas exactas."""
    n_antes = len(df)
    df = df.drop_duplicates()
    n_eliminados = n_antes - len(df)
    if n_eliminados > 0:
        logger.info(
            "Eliminados %d duplicados (%.1f%%)",
            n_eliminados, n_eliminados / n_antes * 100,
        )
    return df


def codificar_etiqueta_binaria(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte la columna Label a binaria: 0 = BENIGN, 1 = Ataque."""
    df = df.copy()
    df["Label_original"] = df[TARGET_COL]
    df[TARGET_COL] = (df[TARGET_COL].str.strip() != "BENIGN").astype(int)
    n_benign = (df[TARGET_COL] == 0).sum()
    n_ataque = (df[TARGET_COL] == 1).sum()
    logger.info(
        "Etiquetas: BENIGN=%d, Ataque=%d (%.1f%%)",
        n_benign, n_ataque, n_ataque / len(df) * 100,
    )
    return df


def seleccionar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona las 14 features más discriminantes + target."""
    cols = [f for f in SELECTED_FEATURES if f in df.columns]
    cols.append(TARGET_COL)
    df = df[cols].copy()
    logger.info("Features seleccionadas: %d", len(cols) - 1)
    return df


def eliminar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    cols_presentes = [c for c in COLS_TO_DROP if c in df.columns]
    if cols_presentes:
        df = df.drop(columns=cols_presentes)
    return df


def preprocesar(df: pd.DataFrame) -> pd.DataFrame:
    """Pipeline completo de preprocesamiento."""
    logger.info("Preprocesamiento: %d filas, %d columnas", *df.shape)
    df = eliminar_columnas(df)
    df = limpiar_infinitos(df)
    df = limpiar_negativos(df)
    df = imputar_nulos(df)
    df = eliminar_duplicados(df)
    df = codificar_etiqueta_binaria(df)
    df = seleccionar_features(df)
    logger.info("Completo: %d filas, %d columnas", *df.shape)
    return df


def main() -> None:
    df_raw = pd.read_csv(INPUT_PATH, low_memory=False)
    df_raw.columns = df_raw.columns.str.strip()
    df_proc = preprocesar(df_raw)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_proc.to_csv(OUTPUT_PATH, index=False)
    logger.info("Guardado en %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
