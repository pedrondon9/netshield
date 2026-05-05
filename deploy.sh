#!/usr/bin/env bash
# Despliega NetShield en el Droplet existente de DigitalOcean.
# El build Docker ocurre directamente en el servidor, no se necesita registry.
#
# Uso: ./deploy.sh <IP_DEL_DROPLET>
#
# Primera vez: instala Docker, crea el servicio systemd y construye la imagen.
# Siguientes veces: sincroniza el código y reconstruye solo si hay cambios.

set -euo pipefail

SERVER_IP="${1:?Uso: ./deploy.sh <IP_DEL_DROPLET>}"

echo "==> [1/3] Sincronizando código al servidor..."
rsync -avz --progress \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.terraform' \
  --exclude='*.tfstate*' \
  --exclude='mlflow/' \
  --exclude='src/data/raw/' \
  --exclude='src/data/validated/' \
  --exclude='src/data/processed/' \
  --exclude='src/data/features/' \
  . root@"$SERVER_IP":/opt/netshield/

echo "==> [2/3] Configurando servidor..."
ssh root@"$SERVER_IP" bash << 'REMOTE'
set -e

# Instalar Docker si no está presente
if ! command -v docker &>/dev/null; then
  echo "  Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker --now
  echo "  Docker instalado."
fi

# Crear directorio persistente para MLflow
mkdir -p /data/mlflow/artifacts

# Registrar el servicio systemd (solo la primera vez)
if [ ! -f /etc/systemd/system/netshield.service ]; then
  cat > /etc/systemd/system/netshield.service << 'EOF'
[Unit]
Description=NetShield IDS
After=docker.service network-online.target
Requires=docker.service

[Service]
WorkingDirectory=/opt/netshield
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
Restart=on-failure
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable netshield
  echo "  Servicio netshield registrado."
fi
REMOTE

echo "==> [3/3] Construyendo imagen y reiniciando servicios..."
ssh root@"$SERVER_IP" bash << 'REMOTE'
set -e
cd /opt/netshield
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d --remove-orphans
REMOTE

echo ""
echo "==> Esperando que la API arranque..."
sleep 15
if curl -sf "http://$SERVER_IP:8000/health" > /dev/null; then
  echo "Deploy exitoso. API operativa en http://$SERVER_IP:8000"
else
  echo "ADVERTENCIA: health check fallido. Revisa los logs:"
  echo "  ssh root@$SERVER_IP docker compose -f /opt/netshield/docker-compose.prod.yml logs api"
  exit 1
fi
