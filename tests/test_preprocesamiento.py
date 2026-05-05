"""Tests unitarios del módulo de preprocesamiento."""

import pytest
import pandas as pd
import numpy as np
from src.data.preprocesamiento import (
    limpiar_infinitos, limpiar_negativos, imputar_nulos,
    eliminar_duplicados, codificar_etiqueta_binaria, preprocesar,
)


@pytest.fixture
def df_muestra():
    """Simula datos CICIDS2017 con los problemas reales del dataset."""
    return pd.DataFrame({
        "Flow Duration": [120000, 0, 5000, 5000, 300000],
        "Total Fwd Packets": [12, 1, 50, 50, 3],
        "Total Backward Packets": [8, 0, 40, 40, 2],
        "Flow Bytes/s": [45000.5, np.inf, 80000.0, 80000.0, 1500.0],
        "Flow Packets/s": [150.3, np.inf, 500.0, 500.0, 20.0],
        "Fwd Packet Length Mean": [234.5, 0, 512.0, 512.0, -5.0],
        "Bwd Packet Length Mean": [180.2, 0, 400.0, 400.0, 100.0],
        "Flow IAT Mean": [8500.0, 0, 2000.0, 2000.0, np.nan],
        "Fwd IAT Mean": [12000.0, 0, 3000.0, 3000.0, 15000.0],
        "Bwd IAT Mean": [9500.0, 0, 2500.0, 2500.0, 11000.0],
        "SYN Flag Count": [1, 100, 0, 0, 1],
        "ACK Flag Count": [10, 0, 50, 50, 5],
        "Init_Win_bytes_forward": [8192, 0, 65535, 65535, 512],
        "Init_Win_bytes_backward": [502, 0, 65535, 65535, 256],
        "Label": ["BENIGN", "DDoS", "BENIGN", "BENIGN", "DDoS"],
    })


def test_limpiar_infinitos_reemplaza_inf(df_muestra):
    df = limpiar_infinitos(df_muestra)
    cols_num = df.select_dtypes(include=[np.number]).columns
    assert not np.isinf(df[cols_num]).any().any()


def test_limpiar_infinitos_genera_nan(df_muestra):
    df = limpiar_infinitos(df_muestra)
    assert df["Flow Bytes/s"].isna().sum() >= 1


def test_limpiar_negativos_corrige(df_muestra):
    df = limpiar_negativos(df_muestra)
    cols_length = [c for c in df.columns if "length" in c.lower()]
    for col in cols_length:
        assert (df[col] >= 0).all(), f"Negativos en {col}"


def test_imputar_nulos_sin_nan(df_muestra):
    df = limpiar_infinitos(df_muestra)
    df = imputar_nulos(df)
    cols_num = df.select_dtypes(include=[np.number]).columns
    assert df[cols_num].isna().sum().sum() == 0


def test_eliminar_duplicados_reduce_filas(df_muestra):
    df = eliminar_duplicados(df_muestra)
    assert len(df) < len(df_muestra)


def test_codificar_etiqueta_binaria_valores(df_muestra):
    df = codificar_etiqueta_binaria(df_muestra)
    assert df["Label"].isin([0, 1]).all()
    assert (df["Label"] == 0).sum() > 0
    assert (df["Label"] == 1).sum() > 0


def test_codificar_conserva_original(df_muestra):
    df = codificar_etiqueta_binaria(df_muestra)
    assert "Label_original" in df.columns


def test_preprocesar_completo_sin_nulos(df_muestra):
    df = preprocesar(df_muestra)
    cols_num = df.select_dtypes(include=[np.number]).columns
    assert df[cols_num].isna().sum().sum() == 0


def test_preprocesar_sin_infinitos(df_muestra):
    df = preprocesar(df_muestra)
    cols_num = df.select_dtypes(include=[np.number]).columns
    assert not np.isinf(df[cols_num]).any().any()


def test_preprocesar_reduce_duplicados(df_muestra):
    df = preprocesar(df_muestra)
    assert len(df) <= len(df_muestra)
