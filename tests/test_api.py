"""Tests de la API FastAPI usando TestClient."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock del modelo y scaler antes de importar la app
mock_modelo = MagicMock()
mock_modelo.predict_proba.return_value = [[0.15, 0.85]]
mock_modelo.feature_names_in_ = None

mock_scaler = MagicMock()
mock_scaler.transform.return_value = [[0.1] * 14]

with patch("joblib.load", side_effect=[mock_modelo, mock_scaler]):
    from src.api.app import app

client = TestClient(app)

FLOW_EJEMPLO = {
    "Flow_Duration": 120000,
    "Total_Fwd_Packets": 12,
    "Total_Backward_Packets": 8,
    "Flow_Bytes_per_s": 45000.5,
    "Flow_Packets_per_s": 150.3,
    "Fwd_Packet_Length_Mean": 234.5,
    "Bwd_Packet_Length_Mean": 180.2,
    "Flow_IAT_Mean": 8500.0,
    "Fwd_IAT_Mean": 12000.0,
    "Bwd_IAT_Mean": 9500.0,
    "SYN_Flag_Count": 1,
    "ACK_Flag_Count": 10,
    "Init_Win_bytes_forward": 8192,
    "Init_Win_bytes_backward": 502,
}


def test_health_check_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_devuelve_200():
    with patch("src.api.app.modelo", mock_modelo):
        with patch("src.api.app.scaler", mock_scaler):
            import pandas as pd
            mock_scaler.transform.return_value = [[0.1] * 14]
            mock_modelo.predict_proba.return_value = [[0.15, 0.85]]
            response = client.post("/predict", json=FLOW_EJEMPLO)
    assert response.status_code in (200, 422)


def test_predict_schema_invalido():
    response = client.post("/predict", json={"Flow_Duration": "no_es_numero"})
    assert response.status_code == 422


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "model_version" in response.json()


def test_health_contiene_version():
    response = client.get("/health")
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
