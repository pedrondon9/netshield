"""Carga y validación inicial del dataset CICIDS2017.

El dataset CICIDS2017 contiene flujos de red capturados durante 5 días,
con 78 features extraídas por CICFlowMeter y una etiqueta (Label) que
indica si el flujo es BENIGN o un tipo de ataque específico.
"""

import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_PATH = Path("src/data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
VALIDATED_PATH = Path("src/data/validated/cicids_validated.csv")

# Features críticas que deben estar presentes en el dataset
EXPECTED_COLUMNS = {
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean",
    "Fwd Packet Length Std", "Bwd Packet Length Max", "Bwd Packet Length Min",
    "Bwd Packet Length Mean", "Bwd Packet Length Std", "Flow Bytes/s",
    "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max",
    "Flow IAT Min", "Fwd IAT Total", "Fwd IAT Mean", "Fwd IAT Std",
    "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Total", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s",
    "Bwd Packets/s", "Min Packet Length", "Max Packet Length",
    "Packet Length Mean", "Packet Length Std", "Packet Length Variance",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count", "PSH Flag Count",
    "ACK Flag Count", "URG Flag Count", "Down/Up Ratio",
    "Average Packet Size", "Avg Fwd Segment Size", "Avg Bwd Segment Size",
    "Init_Win_bytes_forward", "Init_Win_bytes_backward",
    "act_data_pkt_fwd", "min_seg_size_forward", "Active Mean",
    "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std",
    "Idle Max", "Idle Min", "Label",
}


def cargar_datos(ruta: Path = RAW_PATH) -> pd.DataFrame:
    """Carga el CSV del dataset CICIDS2017."""
    logger.info("Cargando dataset desde %s", ruta)
    df = pd.read_csv(ruta, low_memory=False)
    # CICIDS2017 tiene espacios extra en nombres de columnas
    df.columns = df.columns.str.strip()
    logger.info("Dataset cargado: %d filas, %d columnas", len(df), df.shape[1])
    return df


def validar_esquema(df: pd.DataFrame) -> None:
    """Verifica que las columnas esperadas están presentes."""
    columnas_faltantes = EXPECTED_COLUMNS - set(df.columns)
    if columnas_faltantes:
        raise ValueError(f"Columnas faltantes en el dataset: {columnas_faltantes}")
    logger.info("Esquema validado: todas las columnas críticas presentes")


def validar_completitud(df: pd.DataFrame, umbral: float = 0.90) -> None:
    """Alerta si alguna columna tiene completitud inferior al umbral."""
    completitud = 1 - df.isnull().mean()
    columnas_bajas = completitud[completitud < umbral]
    if not columnas_bajas.empty:
        logger.warning(
            "Columnas con completitud < %.0f%%:\n%s", umbral * 100, columnas_bajas
        )
    else:
        logger.info("Completitud OK: todas las columnas > %.0f%%", umbral * 100)


def validar_tipos(df: pd.DataFrame) -> None:
    """Valida que las columnas numéricas clave sean del tipo correcto."""
    cols_numericas = ["Flow Duration", "Total Fwd Packets", "Total Backward Packets"]
    for col in cols_numericas:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"'{col}' debe ser numérico, encontrado: {df[col].dtype}")
    logger.info("Tipos de datos validados correctamente")


def validar_etiquetas(df: pd.DataFrame) -> None:
    """Verifica que la columna Label existe y tiene al menos 2 clases."""
    if "Label" not in df.columns:
        raise ValueError("Columna 'Label' no encontrada en el dataset")
    n_clases = df["Label"].nunique()
    if n_clases < 2:
        raise ValueError(f"Se esperan al menos 2 clases, encontradas: {n_clases}")
    logger.info("Etiquetas validadas: %d clases únicas", n_clases)
    logger.info("Distribución:\n%s", df["Label"].value_counts().to_string())


def guardar_validado(df: pd.DataFrame, ruta: Path = VALIDATED_PATH) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False)
    logger.info("Dataset validado guardado en %s", ruta)


def main() -> None:
    df = cargar_datos()
    validar_esquema(df)
    validar_completitud(df)
    validar_tipos(df)
    validar_etiquetas(df)
    guardar_validado(df)
    logger.info("Ingesta completada: %d registros validados", len(df))


if __name__ == "__main__":
    main()
