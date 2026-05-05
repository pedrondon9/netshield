# NetShield — Pipeline MLOps: Detección de Intrusiones en Red

> **Proyecto — Metodologías de Desarrollo y Despliegue de Aplicaciones para Ciencia de Datos (20GIAR)**  
> Universidad Internacional de Valencia (VIU) · Máster en Data Analytics

**Autor:** Pedro Ndong  
**Repositorio:** https://github.com/pedrondong/netshield-ids

---

## Descripción

Sistema MLOps completo para la detección automática de intrusiones en tráfico de red usando el dataset CICIDS2017. El pipeline cubre el ciclo de vida completo del modelo: ingesta y validación de datos, preprocesamiento, ingeniería de features, entrenamiento con quality gate automático, contenerización y despliegue en producción sobre un servidor DigitalOcean con monitoreo continuo.

**Caso de negocio:** Los equipos SOC procesan miles de alertas diarias con una tasa de falsos positivos superior al 40%. NetShield clasifica tráfico de red como benigno o malicioso en tiempo real (latencia p95 < 20 ms), reduciendo el tiempo medio de detección de horas a milisegundos.

---

## Arquitectura

### Pipeline de datos y modelo

```
src/data/raw/
      │
      ▼
ingesta.py              ← carga CSV + validación de esquema y tipos
      │
      ▼
preprocesamiento.py     ← limpieza, codificación binaria, selección de 14 features
      │
      ▼
feature_engineering.py  ← RobustScaler (robusto a outliers de tráfico DDoS)
      │
      ▼
entrenamiento.py        ← XGBoost + MLflow tracking
      │
      ├── quality gate ─── F1-macro ≥ 0.85
      │                    AUC-ROC  ≥ 0.90     si falla → pipeline se detiene
      │                    Recall   ≥ 0.80
      ▼
src/models/ids_model.pkl + scaler.pkl
```

### Pipeline CI/CD

```
Tu Mac
  └─► git push → main
           │
           ▼
    GitHub Actions — CI (ci.yml)
    ├── 1. Lint con flake8
    ├── 2. Tests con pytest (cobertura ≥ 70%)
    └── 3. Build imagen Docker → push a Container Registry (DOCR)
                          │
                          │  (solo si CI termina con éxito)
                          ▼
    GitHub Actions — CD (cd.yml)
    ├── 1. Terraform apply  ← asegura que Registry, Spaces, Firewall y
    │                          alertas existen y están configurados
    └── 2. SSH al Droplet
             ├── docker login al Container Registry
             ├── docker compose pull  ← descarga la imagen ya construida
             └── docker compose up    ← reinicia el servicio en caliente
                          │
                          ▼
    DigitalOcean Droplet
    ├── API     → :8000   (FastAPI)
    └── MLflow  → :5000   (datos persistentes en /data/mlflow)
```

### Infraestructura gestionada por Terraform

```
Droplet existente (referenciado por nombre, no creado por TF)
├── Container Registry (basic) — imágenes Docker
├── Spaces bucket netshield-data-dev — datos y artefactos
├── Spaces bucket netshield-models-dev — modelos MLflow
├── Firewall — puertos 22, 8000, 5000
└── Monitor Alerts — email si CPU >85% · Memoria >90% · Disco >80%

Estado de Terraform almacenado en Spaces (bucket: netshield-tf-state)
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
│   │   ├── ids_model.pkl            # Modelo entrenado (generado, no se commitea)
│   │   └── scaler.pkl               # Scaler ajustado (generado, no se commitea)
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
├── docker-compose.yml               # Desarrollo local: build local + MLflow
├── docker-compose.prod.yml          # Producción: imagen desde Container Registry
├── infrastructure/
│   ├── main.tf                      # Registry, Spaces, Firewall, alertas, backend S3
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example     # Plantilla de credenciales
├── .github/workflows/
│   ├── ci.yml                       # Lint + tests + build Docker + push a DOCR
│   ├── ml-pipeline.yml              # Entrenamiento + quality gate en push a main
│   └── cd.yml                       # Terraform apply + deploy al Droplet
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
| Docker + Docker Compose | 24+ | Build de imagen y desarrollo local |
| Terraform | 1.5+ | Gestionar recursos en DigitalOcean |
| Cuenta DigitalOcean | — | Droplet existente, Registry, Spaces |

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

Descargar los CSV desde [UNB CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) y colocar en `src/data/raw/`. El archivo mínimo requerido:

```
src/data/raw/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

### Ejecutar el pipeline

Cada paso lee la salida del anterior. Ejecutar desde la raíz del proyecto:

```bash
# 1. Ingesta y validación del dataset
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
# → experimento registrado en mlruns/
```

Si el modelo no supera los umbrales del quality gate (F1 ≥ 0.85, AUC-ROC ≥ 0.90, Recall ≥ 0.80), el paso 4 falla con un mensaje explícito y no produce el `.pkl`.

### Ver resultados en MLflow

```bash
mlflow ui --port 5000
# → http://localhost:5000  experimento: "netshield-ids"
```

### Levantar la API en local

```bash
docker compose up --build
# API en    http://localhost:8000
# Docs en   http://localhost:8000/docs
# MLflow en http://localhost:5000
```

### Probar la API

```bash
# Health check
curl http://localhost:8000/health

# Clasificar un flujo de red
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

## 2. Configuración inicial (una sola vez)

Antes de que el pipeline CI/CD pueda ejecutarse hay que crear dos recursos manualmente en DigitalOcean.

### Paso 1 — Bucket para el estado de Terraform

El pipeline corre `terraform apply` desde GitHub Actions. Terraform necesita guardar su estado en algún lugar persistente. Crear el bucket en el panel de DigitalOcean Spaces:

```
Nombre:  netshield-tf-state
Región:  la misma que tu Droplet (ej. fra1)
Acceso:  Private
```

Solo hay que hacerlo una vez. Terraform lo usa en cada ejecución del CD para leer y escribir el estado.

### Paso 2 — Secrets y Variables en GitHub Actions

Ir a `Settings → Secrets and variables → Actions` en el repositorio.

**Secrets** (valores sensibles):

| Secret | Dónde obtenerlo |
|---|---|
| `DIGITALOCEAN_ACCESS_TOKEN` | `cloud.digitalocean.com/account/api/tokens` |
| `DO_DROPLET_IP` | IP del Droplet (panel de DO) |
| `DO_SSH_PRIVATE_KEY` | Contenido de `~/.ssh/id_rsa` (clave privada SSH del Droplet) |
| `AWS_ACCESS_KEY_ID` | Clave de acceso Spaces · `cloud.digitalocean.com/account/api/spaces-keys` |
| `AWS_SECRET_ACCESS_KEY` | Clave secreta Spaces (mismo panel) |
| `EMAIL_ALERTAS` | Email para recibir alertas de CPU/Memoria/Disco |
| `MLFLOW_TRACKING_URI` | URI del servidor MLflow en producción |
| `CODECOV_TOKEN` | codecov.io (opcional) |

> `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` son tus claves de **DigitalOcean Spaces**, no de AWS. Las usa Terraform y boto3 porque Spaces es compatible con la API S3.

**Variables** (valores no sensibles):

| Variable | Ejemplo | Para qué |
|---|---|---|
| `DO_REGION` | `fra1` | Región del Droplet y endpoint del backend de Terraform |
| `DROPLET_NAME` | `netshield-server` | Nombre exacto del Droplet en el panel de DO |
| `DOCR_NAME` | `netshield` | Nombre del Container Registry (debe ser único en toda la plataforma) |

### Paso 3 — Primer despliegue manual del docker-compose en el Droplet

La primera vez hay que crear el directorio en el servidor:

```bash
ssh root@<IP>
mkdir -p /opt/netshield /data/mlflow
```

A partir de aquí, el pipeline CD se encarga de todo en cada push.

---

## 3. CI/CD — Flujo automático

Una vez completada la configuración inicial, el único comando necesario es:

```bash
git push origin main
```

También se activa al abrir o actualizar un **Pull Request** hacia `main` (en ese caso solo corren los tests, sin despliegue).

### Lo que ocurre automáticamente

Todo el pipeline está definido en un único workflow (`ci.yml`) con cuatro jobs encadenados:

```
push a main  ──►  lint-and-test  ──►  build-and-push  ──►  terraform  ──►  deploy
PR a main    ──►  lint-and-test  (solo tests, sin despliegue)
```

**Job 1 — `lint-and-test`** (push y PR):
1. Flake8 sobre `src/` y `tests/`
2. Pytest con cobertura ≥ 70%

**Job 2 — `build-and-push`** (solo push a `main`):
1. Construye la imagen Docker
2. La sube al Container Registry con dos tags: `:<git-sha>` y `:latest`

**Job 3 — `terraform`** (solo push a `main`):
1. `terraform apply` — verifica y reconcilia la infraestructura (Registry, Spaces, Firewall, alertas)

**Job 4 — `deploy`** (solo push a `main`):
1. Copia `docker-compose.prod.yml` al Droplet
2. SSH al Droplet: autentica con el Registry, hace `docker compose pull` de la nueva imagen y reinicia el servicio
3. Health check final contra `/health`

**ML Pipeline (`ml-pipeline.yml`)** — se dispara en push a `main` con cambios en `src/` o `data/`:
1. Descarga los datos desde Spaces
2. Ejecuta el pipeline completo: ingesta → preprocesamiento → features → entrenamiento
3. Verifica el quality gate (F1 ≥ 0.85, AUC-ROC ≥ 0.90, Recall ≥ 0.80)
4. Si pasa: sube el modelo a Spaces. Si falla: el pipeline se detiene sin desplegar.

### Resumen de pipelines

| Workflow | Disparador | Resultado |
|---|---|---|
| `ci.yml` | Push a `main` | Tests → Build → Terraform → Deploy |
| `ci.yml` | PR a `main` | Solo tests (sin despliegue) |
| `ml-pipeline.yml` | Push a `main` con cambios en `src/` o `data/` | Entrena y registra nuevo modelo |

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

Documentación interactiva Swagger en `/docs`.

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

**Resultados obtenidos:**

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
| Logs estructurados | Cada predicción registra `hash`, `es_ataque`, `proba`, `nivel`, `latencia_ms` en `journald` |
| DO Monitor Alerts | Email automático si CPU >85%, Memoria >90% o Disco >80% |
| MLflow UI | Historial de experimentos en `http://<IP>:5000` |

```bash
# Logs del contenedor de la API
ssh root@<IP> docker logs -f netshield-api-1

# Estado de los contenedores
ssh root@<IP> docker compose -f /opt/netshield/docker-compose.prod.yml ps
```
