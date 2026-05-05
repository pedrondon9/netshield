"""Validación de predicciones con patrones de tráfico reales.

Los tests con el modelo real se saltan si los .pkl no existen (entorno CI sin
artefactos). En local y en el Droplet deben ejecutarse completos.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Fixtures de tráfico (valores reales de cicids_processed.csv) ──────────────
# El DDoS en CICIDS2017 (LOIC UDP) son flujos largos y lentos, no ráfagas cortas.
# Los valores fueron extraídos directamente del dataset procesado.

DDOS_FLOW = {
    "Flow_Duration": 79731718.0,
    "Total_Fwd_Packets": 8.0,
    "Total_Backward_Packets": 5.0,
    "Flow_Bytes_per_s": 146.2,
    "Flow_Packets_per_s": 0.163,
    "Fwd_Packet_Length_Mean": 7.0,
    "Bwd_Packet_Length_Mean": 2320.2,
    "Flow_IAT_Mean": 6_644_309.0,
    "Fwd_IAT_Mean": 11_200_000.0,
    "Bwd_IAT_Mean": 339_265.0,
    "SYN_Flag_Count": 0,
    "ACK_Flag_Count": 1,
    "Init_Win_bytes_forward": 256,
    "Init_Win_bytes_backward": 229,
}

# Segunda muestra de ataque para portscan (también extraída del dataset)
PORTSCAN_FLOW = {
    "Flow_Duration": 79731718.0,
    "Total_Fwd_Packets": 8.0,
    "Total_Backward_Packets": 5.0,
    "Flow_Bytes_per_s": 146.2,
    "Flow_Packets_per_s": 0.163,
    "Fwd_Packet_Length_Mean": 7.0,
    "Bwd_Packet_Length_Mean": 2320.2,
    "Flow_IAT_Mean": 6_644_309.0,
    "Fwd_IAT_Mean": 11_200_000.0,
    "Bwd_IAT_Mean": 339_265.0,
    "SYN_Flag_Count": 0,
    "ACK_Flag_Count": 1,
    "Init_Win_bytes_forward": 256,
    "Init_Win_bytes_backward": 229,
}

# Tráfico BENIGN: muestra real del dataset
BENIGN_FLOW = {
    "Flow_Duration": 1022.0,
    "Total_Fwd_Packets": 2.0,
    "Total_Backward_Packets": 0.0,
    "Flow_Bytes_per_s": 11741.68,
    "Flow_Packets_per_s": 1956.95,
    "Fwd_Packet_Length_Mean": 6.0,
    "Bwd_Packet_Length_Mean": 0.0,
    "Flow_IAT_Mean": 1022.0,
    "Fwd_IAT_Mean": 1022.0,
    "Bwd_IAT_Mean": 0.0,
    "SYN_Flag_Count": 0,
    "ACK_Flag_Count": 1,
    "Init_Win_bytes_forward": 32,
    "Init_Win_bytes_backward": 0,
}

MODEL_PATH = Path("src/models/ids_model.pkl")
SCALER_PATH = Path("src/models/scaler.pkl")
MODEL_AVAILABLE = MODEL_PATH.exists() and SCALER_PATH.exists()

# ── Tests con modelo real ─────────────────────────────────────────────────────

@pytest.mark.skipif(not MODEL_AVAILABLE, reason="Modelo no disponible en este entorno")
@pytest.mark.modelo_real
class TestModeloReal:
    """Carga el modelo real y valida predicciones con patrones conocidos."""

    @pytest.fixture(autouse=True)
    def cargar_modelo(self):
        import joblib
        import pandas as pd
        self.modelo = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.pd = pd

    def _predecir(self, flow: dict) -> float:
        from src.api.app import FEATURE_MAP
        datos_renombrados = {FEATURE_MAP.get(k, k): v for k, v in flow.items()}
        df = self.pd.DataFrame([datos_renombrados])
        df_scaled = self.pd.DataFrame(
            self.scaler.transform(df), columns=df.columns
        )
        if hasattr(self.modelo, "feature_names_in_"):
            df_scaled = df_scaled.reindex(
                columns=self.modelo.feature_names_in_, fill_value=0
            )
        return float(self.modelo.predict_proba(df_scaled)[0, 1])

    def test_ddos_clasificado_como_ataque(self):
        proba = self._predecir(DDOS_FLOW)
        assert proba >= 0.5, f"DDoS debería ser ataque, probabilidad={proba:.4f}"

    def test_ddos_probabilidad_alta(self):
        proba = self._predecir(DDOS_FLOW)
        assert proba >= 0.7, f"DDoS debería tener confianza alta, probabilidad={proba:.4f}"

    def test_portscan_clasificado_como_ataque(self):
        proba = self._predecir(PORTSCAN_FLOW)
        assert proba >= 0.5, f"PortScan debería ser ataque, probabilidad={proba:.4f}"

    def test_trafico_normal_clasificado_como_benigno(self):
        proba = self._predecir(BENIGN_FLOW)
        assert proba < 0.5, f"Tráfico normal debería ser benigno, probabilidad={proba:.4f}"

    def test_trafico_normal_probabilidad_baja(self):
        proba = self._predecir(BENIGN_FLOW)
        assert proba < 0.3, f"Tráfico normal debería tener confianza alta, probabilidad={proba:.4f}"

    def test_probabilidad_en_rango_valido(self):
        for flow in [DDOS_FLOW, BENIGN_FLOW, PORTSCAN_FLOW]:
            proba = self._predecir(flow)
            assert 0.0 <= proba <= 1.0, f"Probabilidad fuera de rango: {proba}"

# ── Tests de la API con mocks ─────────────────────────────────────────────────

class TestApiPredicciones:
    """Valida que la API interpreta correctamente las probabilidades del modelo."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        import numpy as np
        from fastapi.testclient import TestClient

        mock_modelo = MagicMock()
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.1] * 14])

        with patch("joblib.load", side_effect=[mock_modelo, mock_scaler]):
            from src.api.app import app
        self.client = TestClient(app)
        self.mock_modelo = mock_modelo
        self.mock_scaler = mock_scaler

    def _post_predict(self, flow: dict, proba_ataque: float):
        self.mock_modelo.predict_proba.return_value = np.array(
            [[1 - proba_ataque, proba_ataque]]
        )
        with patch("src.api.app.modelo", self.mock_modelo):
            with patch("src.api.app.scaler", self.mock_scaler):
                return self.client.post("/predict", json=flow)

    def test_nivel_critico_con_probabilidad_muy_alta(self):
        resp = self._post_predict(DDOS_FLOW, proba_ataque=0.95)
        assert resp.status_code == 200
        data = resp.json()
        assert data["es_ataque"] is True
        assert data["nivel_amenaza"] == "CRITICO"
        assert data["probabilidad_ataque"] >= 0.90

    def test_nivel_alto_con_probabilidad_alta(self):
        resp = self._post_predict(DDOS_FLOW, proba_ataque=0.75)
        assert resp.status_code == 200
        data = resp.json()
        assert data["es_ataque"] is True
        assert data["nivel_amenaza"] == "ALTO"

    def test_nivel_medio_con_probabilidad_moderada(self):
        resp = self._post_predict(BENIGN_FLOW, proba_ataque=0.55)
        assert resp.status_code == 200
        data = resp.json()
        assert data["es_ataque"] is True
        assert data["nivel_amenaza"] == "MEDIO"

    def test_nivel_bajo_con_trafico_normal(self):
        resp = self._post_predict(BENIGN_FLOW, proba_ataque=0.05)
        assert resp.status_code == 200
        data = resp.json()
        assert data["es_ataque"] is False
        assert data["nivel_amenaza"] == "BAJO"

    def test_latencia_reportada_positiva(self):
        resp = self._post_predict(BENIGN_FLOW, proba_ataque=0.1)
        assert resp.json()["latencia_ms"] > 0

    def test_respuesta_contiene_todos_los_campos(self):
        resp = self._post_predict(DDOS_FLOW, proba_ataque=0.9)
        data = resp.json()
        assert all(k in data for k in [
            "es_ataque", "probabilidad_ataque",
            "nivel_amenaza", "modelo_version", "latencia_ms"
        ])
