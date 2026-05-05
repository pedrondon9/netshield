"""Tests del módulo de feature engineering."""

import pytest
import pandas as pd
import numpy as np
from src.features.feature_engineering import escalar_features


@pytest.fixture
def df_features():
    """Dataset de features ya preprocesado."""
    np.random.seed(42)
    return pd.DataFrame({
        "Flow Duration": np.random.uniform(0, 1e6, 100),
        "Total Fwd Packets": np.random.randint(0, 500, 100).astype(float),
        "Total Backward Packets": np.random.randint(0, 300, 100).astype(float),
        "Flow Bytes/s": np.random.uniform(0, 1e7, 100),
        "Flow Packets/s": np.random.uniform(0, 1e4, 100),
        "Fwd Packet Length Mean": np.random.uniform(0, 1500, 100),
        "Bwd Packet Length Mean": np.random.uniform(0, 1500, 100),
        "Flow IAT Mean": np.random.uniform(0, 1e5, 100),
        "Fwd IAT Mean": np.random.uniform(0, 1e5, 100),
        "Bwd IAT Mean": np.random.uniform(0, 1e5, 100),
        "SYN Flag Count": np.random.randint(0, 10, 100).astype(float),
        "ACK Flag Count": np.random.randint(0, 200, 100).astype(float),
        "Init_Win_bytes_forward": np.random.randint(0, 65535, 100).astype(float),
        "Init_Win_bytes_backward": np.random.randint(0, 65535, 100).astype(float),
        "Label": np.random.choice([0, 1], 100),
    })


def test_escalar_no_cambia_shape(df_features):
    df = escalar_features(df_features, fit=True)
    assert df.shape == df_features.shape


def test_escalar_no_modifica_target(df_features):
    df = escalar_features(df_features, fit=True)
    pd.testing.assert_series_equal(df["Label"], df_features["Label"])


def test_escalar_sin_nan(df_features):
    df = escalar_features(df_features, fit=True)
    assert df.isna().sum().sum() == 0


def test_escalar_centra_datos(df_features):
    df = escalar_features(df_features, fit=True)
    feature_cols = [c for c in df.columns if c != "Label"]
    # RobustScaler centra en la mediana → mediana ≈ 0
    for col in feature_cols:
        assert abs(df[col].median()) < 0.5, f"{col} no centrado"
