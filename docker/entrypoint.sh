#!/bin/sh
set -e

MODEL_DIR=/app/src/models
mkdir -p "$MODEL_DIR"

# Descarga el modelo desde Spaces si no existe ya en el contenedor
if [ ! -f "$MODEL_DIR/ids_model.pkl" ]; then
  echo "[entrypoint] Descargando modelo desde Spaces..."
  aws s3 cp \
    "s3://${SPACES_MODELS_BUCKET}/latest/ids_model.pkl" \
    "$MODEL_DIR/ids_model.pkl" \
    --endpoint-url "https://${DO_REGION}.digitaloceanspaces.com"

  aws s3 cp \
    "s3://${SPACES_MODELS_BUCKET}/latest/scaler.pkl" \
    "$MODEL_DIR/scaler.pkl" \
    --endpoint-url "https://${DO_REGION}.digitaloceanspaces.com"

  echo "[entrypoint] Modelo descargado correctamente."
fi

exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000
