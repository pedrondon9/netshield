"""API REST de detección de intrusiones en red — FastAPI."""

import logging
import time
import os
import hashlib
import threading
import joblib
import pandas as pd
from collections import defaultdict
from pathlib import Path
from fastapi import FastAPI, HTTPException
from src.api.schemas import FlowInput, DetectionOutput

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "src/models/ids_model.pkl"))
SCALER_PATH = Path(os.getenv("SCALER_PATH", "src/models/scaler.pkl"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# Mapeo de nombres JSON-safe a columnas originales CICIDS2017
FEATURE_MAP = {
    "Flow_Duration": "Flow Duration",
    "Total_Fwd_Packets": "Total Fwd Packets",
    "Total_Backward_Packets": "Total Backward Packets",
    "Flow_Bytes_per_s": "Flow Bytes/s",
    "Flow_Packets_per_s": "Flow Packets/s",
    "Fwd_Packet_Length_Mean": "Fwd Packet Length Mean",
    "Bwd_Packet_Length_Mean": "Bwd Packet Length Mean",
    "Flow_IAT_Mean": "Flow IAT Mean",
    "Fwd_IAT_Mean": "Fwd IAT Mean",
    "Bwd_IAT_Mean": "Bwd IAT Mean",
    "SYN_Flag_Count": "SYN Flag Count",
    "ACK_Flag_Count": "ACK Flag Count",
    "Init_Win_bytes_forward": "Init_Win_bytes_forward",
    "Init_Win_bytes_backward": "Init_Win_bytes_backward",
}

app = FastAPI(
    title="NetShield — Detección de Intrusiones en Red",
    description="API de clasificación de tráfico de red. Proyecto 20GIAR — VIU.",
    version=MODEL_VERSION,
)

# Contadores en memoria (visibles en /metrics, recogidos por DO Monitoring vía logs)
_lock = threading.Lock()
_counters: dict = defaultdict(int)
_latencias: list = []

try:
    modelo = joblib.load(MODEL_PATH)
    logger.info("Modelo cargado: %s (v%s)", MODEL_PATH, MODEL_VERSION)
except FileNotFoundError:
    logger.error("Modelo no encontrado en %s", MODEL_PATH)
    modelo = None

try:
    scaler = joblib.load(SCALER_PATH)
    logger.info("Scaler cargado: %s", SCALER_PATH)
except FileNotFoundError:
    logger.warning("Scaler no encontrado — datos sin escalar")
    scaler = None


def _nivel_amenaza(proba: float) -> str:
    if proba >= 0.90:
        return "CRITICO"
    elif proba >= 0.70:
        return "ALTO"
    elif proba >= 0.40:
        return "MEDIO"
    return "BAJO"


def _registrar_metrica(latencia_ms: float, nivel: str, es_ataque: bool) -> None:
    with _lock:
        _counters["predicciones_total"] += 1
        _latencias.append(latencia_ms)
        if es_ataque:
            _counters["ataques_total"] += 1
            _counters[f"nivel_{nivel.lower()}"] += 1
    logger.info(
        "metric latencia_ms=%.1f es_ataque=%s nivel=%s",
        latencia_ms, es_ataque, nivel,
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "modelo_cargado": modelo is not None,
        "scaler_cargado": scaler is not None,
        "version": MODEL_VERSION,
    }


@app.get("/metrics")
def metrics():
    with _lock:
        total = _counters["predicciones_total"]
        latencia_p95 = (
            sorted(_latencias)[int(len(_latencias) * 0.95)]
            if _latencias else 0.0
        )
        return {
            "model_version": MODEL_VERSION,
            "model_loaded": modelo is not None,
            "predicciones_total": total,
            "ataques_total": _counters["ataques_total"],
            "niveles": {
                "critico": _counters["nivel_critico"],
                "alto": _counters["nivel_alto"],
                "medio": _counters["nivel_medio"],
                "bajo": _counters["nivel_bajo"],
            },
            "latencia_p95_ms": round(latencia_p95, 2),
        }


@app.post("/predict", response_model=DetectionOutput)
def predict(flow: FlowInput):
    if modelo is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible")

    inicio = time.time()

    datos = flow.model_dump()
    datos_renombrados = {FEATURE_MAP.get(k, k): v for k, v in datos.items()}
    df_input = pd.DataFrame([datos_renombrados])

    if scaler is not None:
        try:
            df_input = pd.DataFrame(
                scaler.transform(df_input), columns=df_input.columns,
            )
        except Exception as e:
            logger.warning("Error escalando, datos sin escalar: %s", e)

    if hasattr(modelo, "feature_names_in_"):
        df_input = df_input.reindex(columns=modelo.feature_names_in_, fill_value=0)

    proba = float(modelo.predict_proba(df_input)[0, 1])
    es_ataque = proba >= 0.5
    nivel = _nivel_amenaza(proba)
    latencia_ms = (time.time() - inicio) * 1000

    flow_hash = hashlib.sha256(str(datos).encode()).hexdigest()[:12]
    logger.info(
        "Detección: hash=%s ataque=%s proba=%.3f nivel=%s latencia=%.1fms",
        flow_hash, es_ataque, proba, nivel, latencia_ms,
    )
    _registrar_metrica(latencia_ms, nivel, es_ataque)

    return DetectionOutput(
        es_ataque=es_ataque,
        probabilidad_ataque=round(proba, 4),
        nivel_amenaza=nivel,
        modelo_version=MODEL_VERSION,
        latencia_ms=round(latencia_ms, 2),
    )
