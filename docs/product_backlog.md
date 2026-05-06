# Product Backlog — NetShield IDS

**Proyecto:** Pipeline MLOps — Detección de Intrusiones en Red  
**Product Owner / Scrum Master / Desarrollador:** Pedro Ndong (trabajo individual)  

---

## Épicas

| # | Épica | Descripción |
|---|-------|-------------|
| E1 | Datos | Ingesta, validación y preprocesamiento del dataset CICIDS2017 |
| E2 | Modelo | Entrenamiento, evaluación y tracking con MLflow |
| E3 | API | Servicio REST de inferencia de intrusiones en producción |
| E4 | CI/CD | Pipeline automatizado de integración y despliegue |
| E5 | IaC | Infraestructura DigitalOcean como código con Terraform |
| E6 | Monitoreo | Logs estructurados, métricas en /metrics y alertas DO Monitor |

---

## Backlog Priorizado (MoSCoW)

### Must Have (MVP)

| ID | Épica | Historia de Usuario | Criterios de Aceptación | Puntos |
|----|-------|---------------------|------------------------|--------|
| US01 | E1 | Como analista SOC, quiero que el sistema cargue automáticamente el dataset CICIDS2017, para no depender de carga manual. | Script carga CSV; valida columnas esperadas; falla con mensaje claro si falta el fichero. | 3 |
| US02 | E1 | Como científico de datos, quiero validación de esquema, completitud y tipos, para detectar problemas antes del entrenamiento. | Valida 60+ columnas; alerta si completitud < 90%; valida tipos numéricos en columnas clave. | 5 |
| US03 | E1 | Como científico de datos, quiero preprocesar los datos de red de forma reproducible, para que el pipeline sea idempotente. | Limpia infinitos (Flow Bytes/s); corrige negativos; elimina duplicados (~15%); codifica Label binario; tests > 70%. | 8 |
| US04 | E2 | Como científico de datos, quiero entrenar un clasificador XGBoost con tracking en MLflow, para comparar experimentos. | Entrena XGBoost; registra métricas (AUC, F1, recall) y artefactos en MLflow; modelo guardado en models/. | 8 |
| US05 | E2 | Como responsable de seguridad, quiero que solo se desplieguen modelos que superen F1≥0.85, AUC≥0.90 y Recall≥0.80, para evitar falsos negativos en producción. | Si el modelo no supera umbrales → raise ValueError → exit code 1 → pipeline se detiene. | 5 |
| US06 | E3 | Como integrador de SIEM, quiero un endpoint /predict que clasifique un flujo de red como benigno o ataque, para integrarlo en la plataforma SOC. | POST /predict con JSON válido → 200 con es_ataque, probabilidad_ataque, nivel_amenaza; JSON inválido → 422. | 8 |
| US07 | E3 | Como SRE, quiero un endpoint /health para health checks del load balancer. | GET /health → 200 con status "ok" y modelo_cargado; 503 si modelo no disponible. | 2 |
| US08 | E4 | Como desarrollador, quiero CI automático con lint y tests en cada push. | GitHub Actions CI: flake8 + pytest en cada push; falla si cobertura < 70%. | 5 |
| US09 | E5 | Como DevOps, quiero definir Spaces, DOCR, Firewall y Monitor Alerts en Terraform. | terraform plan sin errores; terraform apply crea buckets Spaces, Container Registry, firewall y alertas de CPU/memoria/disco. | 8 |

### Should Have

| ID | Épica | Historia de Usuario | Criterios de Aceptación | Puntos |
|----|-------|---------------------|------------------------|--------|
| US10 | E4 | Como DevOps, quiero CD automático que construya la imagen Docker, la suba al DOCR y despliegue en el Droplet en cada push a main. | git push origin main dispara ci.yml; imagen aparece en DOCR con tag sha+latest; API reiniciada y health check verde. | 8 |
| US11 | E6 | Como analista SOC, quiero logs estructurados de cada predicción. | Cada /predict genera log JSON con flow_hash, clasificación, probabilidad, latencia_ms en stdout del contenedor. | 5 |
| US12 | E6 | Como SRE, quiero alertas automáticas si el Droplet degrada. | DO Monitor Alerts configuradas en Terraform; email si CPU >85%, Memoria >90% o Disco >80%. | 3 |

### Could Have

| ID | Épica | Historia de Usuario | Criterios de Aceptación | Puntos |
|----|-------|---------------------|------------------------|--------|
| US13 | E3 | Como SRE, quiero un endpoint /metrics con estadísticas del servicio. | GET /metrics devuelve model_version y model_loaded. | 2 |
| US14 | E1 | Como científico de datos, quiero feature engineering con RobustScaler para resistir outliers. | RobustScaler ajustado y guardado; features escaladas sin NaN; test de centrado. | 5 |

---

## Velocidad

- Sprint 1: 24 puntos completados
- Sprint 2: 28 puntos completados
- Sprint 3: 16 puntos completados
- **Total: 68 puntos de historia**
