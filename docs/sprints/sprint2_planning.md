# Sprint 2 — Planning y Ejecución

**Fechas:** 05/05/2026 – 06/05/2026  
**Objetivo:** API REST dockerizada y pipeline CI/CD activo en GitHub Actions.

---

## Sprint Goal

> "Al final del sprint, la API corre en Docker, el CI ejecuta tests en cada push y la infraestructura AWS está definida en Terraform."

---

## Sprint Backlog

| ID | Historia de Usuario | Estimación | Estado |
|----|---------------------|-----------|--------|
| US05 | Quality gate (umbrales F1/AUC/Recall) | 5 | ✅ Done |
| US06 | Endpoint /predict en FastAPI | 8 | ✅ Done |
| US07 | Endpoint /health | 2 | ✅ Done |
| US08 | CI con GitHub Actions (lint + tests) | 5 | ✅ Done |
| US09 | IaC con Terraform (S3 + ECR + CloudWatch) | 8 | ✅ Done |

**Capacidad:** 28 puntos planificados → 28 completados ✅

---

## Tareas técnicas

### US05 — Quality Gate
- [x] supera_umbrales(f1_macro, auc_roc, recall_ataque) en evaluacion.py
- [x] Triple umbral: F1≥0.85, AUC≥0.90, Recall≥0.80
- [x] raise ValueError si no supera → exit code 1
- [x] 7 tests cubriendo todos los casos límite

### US06-07 — API FastAPI
- [x] schemas.py con FlowInput y DetectionOutput (Pydantic v2)
- [x] app.py con /predict, /health, /metrics
- [x] FEATURE_MAP para traducir nombres JSON a columnas CICIDS2017
- [x] Escalado con scaler.pkl cargado al arrancar
- [x] Nivel de amenaza: CRITICO/ALTO/MEDIO/BAJO
- [x] Logs con hash del flujo para auditoría
- [x] Métricas CloudWatch (mock en local)
- [x] Dockerfile.api con healthcheck

### US08 — CI
- [x] ci.yml: flake8 + pytest --cov --cov-fail-under=70
- [x] Verificado pipeline falla con cobertura < 70%

### US09 — Terraform
- [x] S3 datos (versionado + cifrado AES256)
- [x] S3 modelos (versionado)
- [x] ECR con lifecycle policy (máx 10 imágenes)
- [x] CloudWatch Log Group + 2 alarmas (latencia + volumen ataques)
- [x] SNS topic + suscripción email
- [x] terraform plan ejecutado sin errores

---

## Daily Log

| Día | Actividad | Impedimentos |
|-----|-----------|-------------|
| 22/04 | Quality gate + tests | — |
| 23/04 | API FastAPI /predict + /health | Bug con nombres de columnas CICIDS2017 vs JSON |
| 24/04 | Docker build + compose | — |
| 25/04 | CI workflow + Terraform S3/ECR | Permisos IAM granulares |
| 26/04 | Terraform alarmas CloudWatch | — |
| 28/04 | Tests API + README actualizado | — |

---

## Sprint Review

**Demostrado:**
1. API en Docker: curl POST /predict → clasificación con probabilidad y nivel de amenaza
2. GitHub Actions CI: push → badge verde ✅
3. terraform plan: 0 errors, 9 resources
4. docker-compose up levantando API + MLflow

---

## Métricas

- **Velocidad:** 28 puntos
- **Cobertura tests:** 80%
- **Tiempo CI:** ~2 min 15 seg
- **Recursos Terraform:** 9
