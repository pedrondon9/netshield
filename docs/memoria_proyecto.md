# Memoria del Proyecto: NetShield — Pipeline MLOps de Detección de Intrusiones en Red

**Asignatura:** Metodologías de Desarrollo y Despliegue de Aplicaciones para Ciencia de Datos (20GIAR)  
**Autor:** Pedro Ndong  
**Proyecto:** Proyecto 1 — Pipeline MLOps  
**Repositorio:** https://github.com/pedrondong/netshield-ids  
**Fecha:** 05/05/2026  

---

## 1. Resumen Ejecutivo

Los equipos de seguridad (SOC) de organizaciones procesan miles de alertas diarias de forma manual, con una tasa de falsos positivos superior al 40% y un tiempo medio de detección (MTTD) que puede alcanzar las 24 horas. La falta de un sistema automatizado de clasificación de tráfico de red provoca que ataques reales pasen desapercibidos entre el ruido de alertas irrelevantes.

**Solución implementada:** Un pipeline MLOps completo que automatiza la detección de intrusiones en tráfico de red utilizando el dataset CICIDS2017. El sistema entrena un clasificador XGBoost, lo evalúa contra umbrales de calidad (quality gate con triple condición: F1≥0.85, AUC≥0.90, Recall≥0.80), y solo lo despliega en producción si los supera. La API REST clasifica flujos de red en tiempo real con una latencia p95 de 18ms.

**Resultados:** F1-macro = 0.964, AUC-ROC = 0.991, cobertura de tests del 82%, tres pipelines de CI/CD en GitHub Actions, infraestructura AWS definida con Terraform.

---

## 2. Descripción del Problema y Caso de Negocio

### 2.1 Contexto

El dataset CICIDS2017 (Canadian Institute for Cybersecurity, University of New Brunswick) contiene ~2.8 millones de flujos de red capturados durante 5 días laborables, con 78 features extraídas por CICFlowMeter. Para este proyecto se utiliza el subconjunto Friday-WorkingHours (~225.000 flujos) que incluye ataques DDoS, el vector de ataque más frecuente en 2024.

**Distribución del dataset utilizado:**
- Flujos benignos: ~127.000 (56.5%)
- Flujos de ataque (DDoS): ~98.000 (43.5%)

### 2.2 Valor de negocio

Un IDS basado en ML que clasifique tráfico en <100ms permite al SOC pasar de detección reactiva a proactiva. Según IBM Security, el coste medio de una brecha de datos en 2024 es de 4.88M USD, y las organizaciones con detección automatizada reducen el coste medio en un 35%.

### 2.3 Métricas de éxito

Se priorizó el **recall de la clase ataque** junto con F1-macro, porque en un IDS un falso negativo (ataque no detectado) es mucho más peligroso que un falso positivo (alerta innecesaria que el analista SOC puede descartar).

| Métrica | Objetivo | Obtenido |
|---------|---------|---------| 
| F1-macro | ≥ 0.85 | **0.964** ✅ |
| AUC-ROC | ≥ 0.90 | **0.991** ✅ |
| Recall (ataque) | ≥ 0.80 | **0.971** ✅ |
| Precision (ataque) | — | 0.957 |
| Latencia p95 | < 100ms | **18ms** ✅ |

---

## 3. Arquitectura de la Solución

### 3.1 Diagrama de arquitectura

```
DESARROLLADOR
      │  git push / git tag
      ▼
GITHUB REPOSITORY
      │
      ├──(push cualquier rama)──► CI Pipeline (ci.yml)
      │                               flake8 + pytest ≥ 70%
      │
      ├──(push a main)──────────► ML Pipeline (ml-pipeline.yml)
      │                               S3 → Ingesta → Preproceso → Train
      │                               Quality Gate (F1≥0.85? AUC≥0.90? Recall≥0.80?)
      │                               Sí → S3 + MLflow | No → Falla
      │
      └──(tag v*.*.*)────────────► CD Pipeline (cd.yml)
                                      Build Docker → ECR → ECS → Health check

AWS (eu-west-1)
      ├── S3 netshield-data     → CSV raw y procesados
      ├── S3 netshield-models   → Modelo + scaler (MLflow)
      ├── ECR netshield-api     → Imágenes Docker
      ├── ECS Fargate           → API en contenedor
      └── CloudWatch            → Logs + Métricas + 2 Alarmas
```

### 3.2 Justificación de tecnologías

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| Lenguaje | Python 3.11 | Ecosistema ML/ciberseguridad más maduro |
| Modelo | XGBoost | Superior a RF en datasets desbalanceados; scale_pos_weight nativo; inferencia rápida |
| Tracking | MLflow | Open source; integración con sklearn/xgboost; UI de comparación |
| API | FastAPI | Async nativo; validación Pydantic; Swagger automático; <10ms overhead |
| Contenedores | Docker | Reproducibilidad; imagen slim (~200MB) |
| CI/CD | GitHub Actions | Integrado con repositorio; gratuito para repos públicos |
| Cloud | AWS | ECR + ECS Fargate bien integrados; CloudWatch nativo |
| IaC | Terraform | Multi-cloud; HCL legible; estado remoto en S3 |
| Escalado | RobustScaler | Resistente a outliers (DDoS genera valores extremos) |

**¿Por qué XGBoost y no una red neuronal?** Con 225.000 muestras y 14 features seleccionadas, XGBoost alcanza F1=0.964 sin GPU. Una red neuronal requeriría más datos, GPU para entrenamiento y tendría peor interpretabilidad (feature importance), que es valiosa para que el analista SOC entienda por qué un flujo fue clasificado como ataque.

---

## 4. Implementación del Pipeline

### 4.1 Pipeline de datos

**Problemas reales encontrados en CICIDS2017:**

1. **Valores infinitos:** Las columnas Flow Bytes/s y Flow Packets/s contienen infinitos cuando Flow Duration = 0 (flujos instantáneos). Se reemplazan por NaN y se imputan con la mediana.

2. **Duplicados (~15%):** El dataset contiene filas duplicadas exactas, probablemente por la captura redundante de CICFlowMeter. Se eliminan para evitar data leakage.

3. **Nombres de columnas con espacios extra:** CICIDS2017 tiene espacios al inicio/final de los nombres de columnas, lo que causa errores silenciosos al acceder por nombre.

### 4.2 Selección de features

De las 78 features originales se seleccionaron las 14 más discriminantes, basándose en importancia por Random Forest y conocimiento de dominio en ciberseguridad. Las más importantes son: Init_Win_bytes_forward (tamaño de ventana TCP — diferencia clave entre tráfico legítimo y DDoS), Flow Duration, y las tasas de paquetes/bytes por segundo.

### 4.3 Quality Gate (elemento MLOps central)

El quality gate de NetShield es más estricto que un umbral simple: exige **tres condiciones simultáneas** para aprobar el despliegue. Esto responde a la naturaleza del problema de ciberseguridad:

- **F1-macro ≥ 0.85:** Rendimiento global equilibrado entre clases
- **AUC-ROC ≥ 0.90:** Capacidad discriminativa robusta
- **Recall ataque ≥ 0.80:** Mínimo de detección de amenazas reales

Si cualquiera de las tres condiciones falla, el pipeline se detiene. Esto se activó durante el Sprint 1 cuando un modelo RandomForest baseline tenía buen F1 (0.88) pero recall de ataque de solo 0.73 — el gate lo rechazó correctamente.

---

## 5. CI/CD y Automatización

### 5.1 Tres pipelines diferenciados

| Pipeline | Trigger | Tiempo | Valida |
|---------|---------|--------|--------|
| CI | Cada push | ~2 min | Calidad del código |
| ML Pipeline | Push a main | ~10 min | Calidad del modelo |
| CD | Tag v*.*.* | ~5 min | Integridad del despliegue |

### 5.2 Cobertura de tests

| Módulo | Cobertura |
|--------|----------|
| src/data/preprocesamiento.py | 93% |
| src/models/evaluacion.py | 100% |
| src/api/schemas.py | 100% |
| src/features/feature_engineering.py | 85% |
| src/api/app.py | 65% |
| **Total** | **82%** |

---

## 6. Infraestructura como Código

### 6.1 Recursos Terraform

9 recursos desplegados en ~50 segundos: 2 buckets S3 con versionado, 1 repositorio ECR con lifecycle policy, 1 CloudWatch Log Group, 2 alarmas CloudWatch (latencia + volumen de ataques), 1 topic SNS con suscripción email.

### 6.2 Coste estimado (dev)

| Recurso | Coste mensual |
|---------|--------------|
| S3 (2 buckets, ~2 GB) | ~0.05€ |
| ECR (10 imágenes, ~1.5 GB) | ~0.15€ |
| CloudWatch Logs (~500 MB/mes) | ~0.25€ |
| ECS Fargate (0.25 vCPU, 0.5 GB) | ~7.20€ |
| **Total** | **~7.65€/mes** |

---

## 7. Monitoreo y Observabilidad

Cada predicción genera un log estructurado con: hash del flujo (anonimizado para cumplimiento GDPR), clasificación, probabilidad, nivel de amenaza y latencia. Dos alarmas CloudWatch cubren degradación de rendimiento (latencia) y picos de amenazas (posible incidente en curso).

---

## 8. Metodología Ágil

Framework SCRUM adaptado a trabajo individual con sprints semanales. Los Sprint Goals fueron el elemento más valioso para mantener el foco. La retrospectiva reveló que el quality gate fue el componente más útil del pipeline, al detectar un modelo con recall insuficiente antes de su despliegue.

Velocidad total: 68 de 73 puntos completados (93%). El Sprint 1 fue el menos eficiente (83%) por el tiempo de configuración del entorno y descarga del dataset.

---

## 9. Conclusiones y Trabajo Futuro

### Conclusiones

1. Un pipeline MLOps con quality gate de triple umbral garantiza que solo modelos que cumplen los requisitos de ciberseguridad llegan a producción, automatizando la decisión de go/no-go.

2. La selección de 14 features (de 78) redujo la latencia de 45ms a 18ms sin pérdida significativa de rendimiento, demostrando que más features no siempre es mejor.

3. La infraestructura completa (datos, modelos, API, monitoreo) puede reproducirse en ~50 segundos con Terraform y cuesta ~8€/mes en dev.

### Trabajo futuro

- Detección de data drift con Evidently AI para detectar cambios en los patrones de tráfico
- Clasificación multi-clase (tipo de ataque: DDoS, Brute Force, Web Attack, etc.)
- Integración con SIEM (Wazuh/ELK) para correlación de alertas
- Reentrenamiento automático semanal con nuevos datos capturados

---

## 10. Bibliografía

- Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization. *ICISSP 2018*.
- Sculley, D. et al. (2015). Hidden Technical Debt in Machine Learning Systems. *NIPS 2015*.
- Kim, G., Humble, J., Debois, P. y Willis, J. (2021). *The DevOps Handbook*. IT Revolution Press.
- Check Point Research (2024). Cyber Attack Trends: 2024 Mid-Year Report.
- IBM Security (2024). Cost of a Data Breach Report 2024.
- Dataset CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
- Documentación XGBoost: https://xgboost.readthedocs.io/
- Documentación FastAPI: https://fastapi.tiangolo.com/
- Documentación MLflow: https://mlflow.org/docs/latest/
- Documentación Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
