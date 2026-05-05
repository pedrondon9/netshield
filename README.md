# NetShield — Pipeline MLOps: Detección de Intrusiones en Red

> **Proyecto — Metodologías de Desarrollo y Despliegue de Aplicaciones para Ciencia de Datos (20GIAR)**  
> Universidad Internacional de Valencia (VIU) · Máster en Data Analytics

**Autor:** Pedro Ndong  
**Repositorio:** https://github.com/pedrondong/netshield-ids

---

## Descripción

Sistema MLOps completo para la detección automática de intrusiones en tráfico de red usando el dataset CICIDS2017. El pipeline cubre el ciclo de vida completo del modelo: ingesta y validación de datos, preprocesamiento, ingeniería de features, entrenamiento con quality gate automático, contenerización y despliegue en producción sobre un Droplet de DigitalOcean con monitoreo continuo.

**Caso de negocio:** Los equipos SOC procesan miles de alertas diarias con una tasa de falsos positivos superior al 40%. NetShield clasifica tráfico de red como benigno o malicioso en tiempo real (latencia p95 < 20 ms), reduciendo el tiempo medio de detección de horas a milisegundos.

---

## Arquitectura

```
DATOS
  src/data/raw/
       │
       ▼
  ingesta.py              carga CSV + validación de esquema y tipos
       │
       ▼
  preprocesamiento.py     limpieza, codificación binaria, selección de 14 features
       │
       ▼
  feature_engineering.py  RobustScaler (robusto a outliers de tráfico DDoS)
       │
       ▼
MODELO
  entrenamiento.py        XGBoost + MLflow tracking
       │
       ├── quality gate ── F1-macro ≥ 0.85
       │                   AUC-ROC  ≥ 0.90    si falla → pipeline se detiene
       │                   Recall   ≥ 0.80
       ▼
  src/models/ids_model.pkl + scaler.pkl

API
  FastAPI  /predict  /health  /metrics
  Docker Compose (build en el propio Droplet)
       │
       ▼
PRODUCCIÓN — DigitalOcean Droplet (existente)
  ├── API     → :8000   (imagen construida en el servidor)
  └── MLflow  → :5000   (datos persistentes en /data/mlflow)

  Terraform gestiona sobre el Droplet existente:
  ├── Firewall  (puertos 22, 8000, 5000)
  ├── Spaces buckets  (datos y modelos)
  └── Alertas  CPU >85% · Memoria >90% · Disco >80%

CI/CD (GitHub Actions)
  push → cualquier rama   ──► ci.yml           lint + tests + cobertura ≥ 70%
  push → main (src/data/) ──► ml-pipeline.yml  entrenamiento + quality gate
  git tag v*.*.*          ──► cd.yml           rsync → build en Droplet → health check
```

---

## Dataset

**CICIDS2017** — Canadian Institute for Cybersecurity (University of New Brunswick):

| Atributo | Valor |
|---|---|
| Registros totales | ~2.8 M flujos de red |
| Features originales | 78 + 1 target (Label) |
| Features seleccionadas | 14 (importancia RF + conocimiento de dominio) |
| Archivo utilizado | `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` |
| Clasificación | Binaria: BENIGN (0) vs Ataque (1) |

Ataques cubiertos: DDoS, PortScan, Brute Force (FTP/SSH), DoS (Hulk, GoldenEye, Slowloris), Web Attack (XSS, SQLi), Botnet, Heartbleed.

---

## Estructura del repositorio

```
netshield/
├── src/
│   ├── data/
│   │   ├── raw/                     # CSVs originales CICIDS2017 (no se commitean)
│   │   ├── validated/               # Salida de ingesta.py
│   │   ├── processed/               # Salida de preprocesamiento.py
│   │   ├── features/                # Salida de feature_engineering.py
│   │   ├── ingesta.py               # Carga + validación de esquema
│   │   └── preprocesamiento.py      # Limpieza, encoding binario, selección
│   ├── features/
│   │   └── feature_engineering.py   # RobustScaler + guardado de scaler.pkl
│   ├── models/
│   │   ├── entrenamiento.py         # XGBoost + MLflow + quality gate
│   │   ├── evaluacion.py            # Umbrales mínimos para despliegue
│   │   ├── ids_model.pkl            # Modelo entrenado (generado localmente)
│   │   └── scaler.pkl               # Scaler ajustado (generado localmente)
│   └── api/
│       ├── app.py                   # FastAPI: /predict /health /metrics
│       └── schemas.py               # Pydantic: FlowInput, DetectionOutput
├── tests/
│   ├── test_preprocesamiento.py
│   ├── test_features.py
│   ├── test_modelo.py
│   └── test_api.py
├── docker/
│   ├── Dockerfile.api               # Imagen producción (python:3.11-slim)
│   └── Dockerfile.train             # Imagen entrenamiento
├── docker-compose.yml               # Desarrollo local (MLflow con volumen local)
├── docker-compose.prod.yml          # Producción (MLflow con /data/mlflow + restart)
├── deploy.sh                        # Despliega en el Droplet vía rsync + SSH
├── infrastructure/
│   ├── main.tf                      # Spaces, Firewall y alertas sobre Droplet existente
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── .github/workflows/
│   ├── ci.yml                       # Lint + tests en cada push
│   ├── ml-pipeline.yml              # Entrenamiento + quality gate en push a main
│   └── cd.yml                       # rsync al Droplet + build Docker + health check
├── notebooks/
│   └── 01_EDA.ipynb
├── docs/sprints/
├── requirements.txt
└── requirements-dev.txt
```

---

## Requisitos previos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11+ | Ejecutar el pipeline local |
| Docker + Docker Compose | 24+ | Desarrollo local |
| Terraform | 1.5+ | Gestionar recursos en DigitalOcean |
| rsync | cualquiera | Sincronizar código al Droplet |
| Droplet DigitalOcean | existente | Servidor de producción |

---

## 1. Ejecución local

### Clonar y crear entorno virtual

```bash
git clone https://github.com/pedrondong/netshield-ids
cd netshield-ids
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Descargar el dataset

Descargar los CSV desde [UNB CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) y colocar en `src/data/raw/`. Archivo mínimo requerido:

```
src/data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

### Ejecutar el pipeline

Cada paso lee la salida del anterior. Ejecutar desde la raíz del proyecto:

```bash
# 1. Ingesta y validación
python -m src.data.ingesta
# → src/data/validated/cicids_validated.csv

# 2. Limpieza, codificación binaria y selección de features
python -m src.data.preprocesamiento
# → src/data/processed/cicids_processed.csv

# 3. Escalado con RobustScaler
python -m src.features.feature_engineering
# → src/data/features/cicids_features.csv
# → src/models/scaler.pkl

# 4. Entrenamiento + MLflow tracking + quality gate
python -m src.models.entrenamiento
# → src/models/ids_model.pkl
```

Si el modelo no supera los umbrales del quality gate (F1 ≥ 0.85, AUC-ROC ≥ 0.90, Recall ≥ 0.80), el paso 4 falla con un mensaje explícito y no produce el `.pkl`.

### Ver resultados en MLflow

```bash
mlflow ui --port 5000
# → http://localhost:5000   experimento: "netshield-ids"
```

### Levantar la API en local

```bash
docker compose up --build
# API    → http://localhost:8000
# Docs   → http://localhost:8000/docs
# MLflow → http://localhost:5000
```

### Probar la API

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
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
    "Init_Win_bytes_backward": 502
  }'
```

Respuesta:

```json
{
  "es_ataque": false,
  "probabilidad_ataque": 0.0312,
  "nivel_amenaza": "BAJO",
  "modelo_version": "1.0.0",
  "latencia_ms": 12.4
}
```

| `nivel_amenaza` | Probabilidad | Acción recomendada |
|---|---|---|
| `CRITICO` | ≥ 0.90 | Bloqueo inmediato + alerta SOC |
| `ALTO` | ≥ 0.70 | Investigación prioritaria |
| `MEDIO` | ≥ 0.40 | Monitoreo intensivo |
| `BAJO` | < 0.40 | Tráfico benigno |

### Ejecutar los tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 2. Despliegue en producción (DigitalOcean)

El proyecto se despliega sobre el **Droplet existente**. Docker se instala en el propio servidor y la imagen se construye allí directamente — no se necesita un Container Registry externo.

### Paso 1 — Configurar Terraform

Terraform gestiona únicamente los recursos auxiliares: Spaces (almacenamiento), Firewall y alertas de monitoreo. No toca el Droplet.

Credenciales necesarias de DigitalOcean:
- **API Token** → `cloud.digitalocean.com/account/api/tokens`
- **Spaces Keys** → `cloud.digitalocean.com/account/api/spaces-keys`

```bash
cd infrastructure/
cp terraform.tfvars.example terraform.tfvars
```

Editar `terraform.tfvars`:

```hcl
do_token          = "dop_v1_..."
spaces_access_id  = "..."
spaces_secret_key = "..."
email_alertas     = "tu@email.com"

# Nombre exacto del Droplet tal como aparece en el panel de DO
droplet_name      = "mi-droplet"

# Región del Droplet (ams3, fra1, nyc3...)
do_region         = "ams3"
```

```bash
terraform init
terraform plan     # revisar antes de aplicar
terraform apply    # confirmar con "yes"
```

Recursos que crea Terraform:

| Recurso | Descripción |
|---|---|
| Spaces `netshield-data-dev` | Almacenamiento de datos raw y procesados |
| Spaces `netshield-models-dev` | Artefactos de modelos MLflow |
| Firewall | Abre puertos 22, 8000 y 5000 en el Droplet |
| Monitor Alert ×3 | Email si CPU >85%, Memoria >90% o Disco >80% |

### Paso 2 — Desplegar con deploy.sh

El script sincroniza el código y gestiona el servidor en un solo comando:

1. Copia el proyecto al Droplet con `rsync` (excluye datos crudos, entornos virtuales y carpetas de Terraform)
2. Instala Docker en el servidor si no está instalado
3. Crea el directorio persistente `/data/mlflow` para la base de datos de MLflow
4. Registra un servicio `systemd` llamado `netshield` que arranca automáticamente con el servidor
5. Construye la imagen Docker directamente en el Droplet (`docker compose build`)
6. Arranca los contenedores y verifica que la API responde

```bash
# Ejecutar desde la raíz del proyecto
./deploy.sh <IP_DEL_DROPLET>
```

Al terminar:

```
==> Deploy exitoso. API operativa en http://<IP>:8000
```

**Despliegues posteriores** (nueva versión del modelo o del código): mismo comando, el script solo sincroniza los cambios y reconstruye la imagen.

```bash
./deploy.sh <IP_DEL_DROPLET>
```

### Paso 3 — Verificar

```bash
# Health check
curl http://<IP>:8000/health

# Logs en tiempo real
ssh root@<IP> journalctl -u netshield -f

# Estado de los contenedores
ssh root@<IP> docker compose -f /opt/netshield/docker-compose.prod.yml ps
```

---

## 3. CI/CD con GitHub Actions

### Secrets necesarios en GitHub

Configurar en `Settings → Secrets and variables → Actions`:

| Secret | Valor |
|---|---|
| `DO_DROPLET_IP` | IP del Droplet |
| `DO_SSH_PRIVATE_KEY` | Contenido de `~/.ssh/id_rsa` (clave privada SSH) |
| `CODECOV_TOKEN` | Token de Codecov (opcional) |

### Pipelines

| Workflow | Disparador | Qué hace |
|---|---|---|
| `ci.yml` | Push a cualquier rama | Flake8 + pytest + cobertura ≥ 70% |
| `ml-pipeline.yml` | Push a `main` con cambios en `src/` o `data/` | Entrena el modelo y verifica el quality gate |
| `cd.yml` | Tag `v*.*.*` | rsync al Droplet → `docker compose build` → health check |

### Flujo de release

```bash
# Cuando CI pasa en main, crear un tag semver para disparar el deploy
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions sincroniza el código, construye la imagen en el Droplet
# y verifica que la API arranca correctamente
```

---

## 4. API — Referencia

### `GET /health`

```json
{
  "status": "ok",
  "modelo_cargado": true,
  "scaler_cargado": true,
  "version": "1.0.0"
}
```

### `GET /metrics`

Contadores acumulados desde el inicio del proceso:

```json
{
  "model_version": "1.0.0",
  "model_loaded": true,
  "predicciones_total": 1248,
  "ataques_total": 73,
  "niveles": { "critico": 12, "alto": 28, "medio": 33, "bajo": 1175 },
  "latencia_p95_ms": 18.4
}
```

### `POST /predict`

**Cuerpo de la petición** — 14 features del dataset CICIDS2017:

| Campo | Tipo | Descripción |
|---|---|---|
| `Flow_Duration` | float | Duración del flujo en microsegundos |
| `Total_Fwd_Packets` | int | Paquetes en dirección forward |
| `Total_Backward_Packets` | int | Paquetes en dirección backward |
| `Flow_Bytes_per_s` | float | Bytes por segundo |
| `Flow_Packets_per_s` | float | Paquetes por segundo |
| `Fwd_Packet_Length_Mean` | float | Longitud media de paquetes forward |
| `Bwd_Packet_Length_Mean` | float | Longitud media de paquetes backward |
| `Flow_IAT_Mean` | float | Inter-arrival time medio del flujo |
| `Fwd_IAT_Mean` | float | IAT medio forward |
| `Bwd_IAT_Mean` | float | IAT medio backward |
| `SYN_Flag_Count` | int | Número de flags SYN |
| `ACK_Flag_Count` | int | Número de flags ACK |
| `Init_Win_bytes_forward` | int | Ventana TCP inicial forward |
| `Init_Win_bytes_backward` | int | Ventana TCP inicial backward |

**Respuesta:**

| Campo | Tipo | Descripción |
|---|---|---|
| `es_ataque` | bool | `true` si el tráfico es malicioso |
| `probabilidad_ataque` | float | Confianza del modelo (0–1) |
| `nivel_amenaza` | string | `CRITICO` / `ALTO` / `MEDIO` / `BAJO` |
| `modelo_version` | string | Versión del modelo activo |
| `latencia_ms` | float | Tiempo de inferencia en ms |

Documentación interactiva Swagger disponible en `/docs`.

---

## 5. Modelo

**Algoritmo:** XGBoost con `scale_pos_weight=3.0` para compensar el desbalance entre tráfico benigno y ataques.

| Parámetro | Valor |
|---|---|
| `n_estimators` | 300 |
| `learning_rate` | 0.05 |
| `max_depth` | 6 |
| `subsample` | 0.8 |
| `colsample_bytree` | 0.8 |

**Resultados:**

| Métrica | Resultado | Umbral mínimo |
|---|---|---|
| F1-macro | **0.964** | ≥ 0.85 |
| AUC-ROC | **0.991** | ≥ 0.90 |
| Recall (ataque) | **0.971** | ≥ 0.80 |
| Precision (ataque) | **0.957** | — |
| Latencia p95 | **~18 ms** | < 100 ms |

Si el modelo no supera los tres umbrales simultáneamente, `entrenamiento.py` lanza una excepción y el pipeline de CI/CD falla, bloqueando el despliegue de un modelo deficiente.

---

## 6. Monitoreo

| Mecanismo | Descripción |
|---|---|
| `GET /metrics` | Contadores en tiempo real: predicciones, ataques por nivel, latencia p95 |
| Logs estructurados | Cada predicción emite una línea con `hash`, `es_ataque`, `proba`, `nivel` y `latencia_ms` |
| DO Monitor Alerts | Email automático si CPU >85%, Memoria >90% o Disco >80% |
| MLflow UI | Historial de experimentos en `http://<IP>:5000` |

```bash
# Logs del servicio
ssh root@<IP> journalctl -u netshield -f

# Logs del contenedor de la API
ssh root@<IP> docker logs -f netshield-api-1
```
