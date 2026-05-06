# NetShield — Pipeline MLOps de Detección de Intrusiones en Red

**Asignatura:** Metodologías de Desarrollo y Despliegue de Aplicaciones para Ciencia de Datos (20GIAR)  
**Autor:** Pedro Ndong  
**Proyecto:** Proyecto 1 — Pipeline MLOps  
**Repositorio:** https://github.com/pedrondon9/netshield-ids  
**Fecha:** 06/05/2026  

---

## 1. Resumen Ejecutivo

Los equipos de seguridad (SOC) de organizaciones procesan miles de alertas diarias de forma manual, con una tasa de falsos positivos superior al 40% y un tiempo medio de detección (MTTD) que puede alcanzar las 24 horas. La falta de un sistema automatizado de clasificación de tráfico de red provoca que ataques reales pasen desapercibidos entre el ruido de alertas irrelevantes.

**Solución implementada:** Un pipeline MLOps completo que automatiza la detección de intrusiones en tráfico de red utilizando el dataset CICIDS2017. El sistema entrena un clasificador XGBoost, lo evalúa contra umbrales de calidad (quality gate con triple condición: F1≥0.85, AUC≥0.90, Recall≥0.80), y solo lo despliega en producción si los supera. La API REST clasifica flujos de red en tiempo real con una latencia p95 de 18 ms.

**Resultados:** F1-macro = 0.964, AUC-ROC = 0.991, cobertura de tests del 88%, un pipeline CI/CD unificado con cuatro jobs en GitHub Actions, infraestructura definida con Terraform sobre DigitalOcean.

---

## 2. Descripción del Problema y Caso de Negocio

### 2.1 Contexto

El dataset CICIDS2017 (Canadian Institute for Cybersecurity, University of New Brunswick) contiene ~2.8 millones de flujos de red capturados durante 5 días laborables, con 78 features extraídas por CICFlowMeter. Para este proyecto se utiliza el subconjunto Friday-WorkingHours (~225.000 flujos) que incluye ataques DDoS, el vector de ataque más frecuente en 2024.

**Distribución del dataset utilizado:**
- Flujos benignos: ~127.000 (56.5%)
- Flujos de ataque (DDoS): ~98.000 (43.5%)

**Característica clave del tráfico DDoS en CICIDS2017:** Los ataques LOIC-UDP no son ráfagas de alta velocidad sino flujos largos y lentos (duración media ~80 segundos, solo ~146 bytes/s) con paquetes backward grandes (Bwd_Packet_Length_Mean ~2320 bytes). Este patrón contraintuitivo fue identificado analizando directamente el CSV procesado y fue determinante para construir los tests de validación del modelo con valores reales.

### 2.2 Valor de negocio

Un IDS basado en ML que clasifique tráfico en <100 ms permite al SOC pasar de detección reactiva a proactiva. Según IBM Security, el coste medio de una brecha de datos en 2024 es de 4.88M USD, y las organizaciones con detección automatizada reducen el coste medio en un 35%.

### 2.3 Métricas de éxito

Se priorizó el **recall de la clase ataque** junto con F1-macro, porque en un IDS un falso negativo (ataque no detectado) es mucho más peligroso que un falso positivo (alerta innecesaria que el analista SOC puede descartar).

| Métrica | Objetivo | Obtenido |
|---------|---------|---------|
| F1-macro | ≥ 0.85 | **0.964** ✅ |
| AUC-ROC | ≥ 0.90 | **0.991** ✅ |
| Recall (ataque) | ≥ 0.80 | **0.971** ✅ |
| Precision (ataque) | — | 0.957 |
| Latencia p95 | < 100 ms | **~18 ms** ✅ |

---

## 3. Arquitectura de la Solución

### 3.1 Diagrama de arquitectura

```
DESARROLLADOR
      │  git push origin main
      ▼
GITHUB REPOSITORY
      │
      └──(push a main)──► ci.yml — 4 jobs encadenados
                              │
                              ├── 1. lint-and-test   (push y PR)
                              │       flake8 + pytest ≥ 70% cobertura
                              │
                              ├── 2. build-and-push  (solo push)
                              │       Build imagen Docker
                              │       Push a DOCR :sha + :latest
                              │
                              ├── 3. terraform       (solo push)
                              │       terraform apply
                              │       Registry, Spaces, Firewall, Alertas
                              │
                              └── 4. deploy          (solo push)
                                      rsync docker-compose.prod.yml
                                      SSH → docker pull + docker compose up
                                      Health check /health

DigitalOcean FRA1
      ├── Droplet (ubuntu-s-1vcpu-2gb, Frankfurt)
      │       ├── API      → :8000  (FastAPI en Docker)
      │       └── MLflow   → :5000  (datos en /data/mlflow)
      │
      ├── Container Registry: netshield-pndng
      │       └── registry.digitalocean.com/netshield-pndng/api
      │
      ├── Spaces: netshield-pndng-models-dev  → modelos .pkl
      ├── Spaces: netshield-pndng-data-dev    → datos procesados
      ├── Spaces: netshield-tf-state          → estado de Terraform
      │
      └── Monitor Alerts → email si CPU >85%, Memoria >90%, Disco >80%

Flujo del modelo en producción:
      Droplet arranca  →  entrypoint.sh descarga ids_model.pkl
                          y scaler.pkl desde Spaces  →  uvicorn
```

### 3.2 Justificación de tecnologías

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| Lenguaje | Python 3.11 | Ecosistema ML/ciberseguridad más maduro |
| Modelo | XGBoost | Superior a RF en datasets desbalanceados; `scale_pos_weight` nativo; inferencia rápida |
| Tracking | MLflow | Open source; integración con sklearn/xgboost; UI de comparación de experimentos |
| API | FastAPI | Async nativo; validación Pydantic; Swagger automático; <10 ms overhead |
| Contenedores | Docker | Reproducibilidad; imagen slim (~200 MB); entrypoint descarga modelo al arrancar |
| CI/CD | GitHub Actions | Integrado con repositorio; gratuito para repos públicos |
| Cloud | DigitalOcean | Droplet existente reutilizado; Spaces S3-compatible; DOCR integrado; coste predecible |
| IaC | Terraform | Multi-cloud; estado remoto en DO Spaces; referencia al Droplet sin recrearlo |
| Escalado | RobustScaler | Resistente a outliers (DDoS genera valores extremos en bytes/s y duraciones) |

**¿Por qué DigitalOcean y no AWS?** El Droplet ya existía con MLflow y otros servicios desplegados. Reutilizarlo evitó costes de transferencia y tiempo de configuración. Terraform referencia el Droplet por nombre (`data "digitalocean_droplet"`) en lugar de crearlo, lo que es el patrón correcto cuando la infraestructura base ya existe.

**¿Por qué XGBoost y no una red neuronal?** Con 225.000 muestras y 14 features seleccionadas, XGBoost alcanza F1=0.964 sin GPU. Una red neuronal requeriría más datos, GPU para entrenamiento y tendría peor interpretabilidad (feature importance), que es valiosa para que el analista SOC entienda por qué un flujo fue clasificado como ataque.

---

## 4. Implementación del Pipeline

### 4.1 Pipeline de datos

```
src/data/raw/CSV
      │
      ▼
ingesta.py              ← carga + validación de esquema y tipos
      │
      ▼
preprocesamiento.py     ← limpieza, codificación binaria, selección de 14 features
      │
      ▼
feature_engineering.py  ← RobustScaler ajustado → scaler.pkl
      │
      ▼
entrenamiento.py        ← XGBoost + MLflow + quality gate → ids_model.pkl
```

**Problemas reales encontrados en CICIDS2017:**

1. **Valores infinitos:** Las columnas `Flow_Bytes/s` y `Flow_Packets/s` contienen infinitos cuando `Flow_Duration = 0` (flujos instantáneos). Se reemplazan por NaN y se imputan con la mediana.

2. **Duplicados (~15%):** El dataset contiene filas duplicadas exactas, probablemente por captura redundante de CICFlowMeter. Se eliminan para evitar data leakage.

3. **Nombres de columnas con espacios extra:** CICIDS2017 tiene espacios al inicio/final de los nombres de columnas, lo que causa errores silenciosos al acceder por nombre.

### 4.2 Selección de features

De las 78 features originales se seleccionaron las 14 más discriminantes, basándose en importancia por Random Forest y conocimiento de dominio en ciberseguridad. Las más importantes son: `Init_Win_bytes_forward` (tamaño de ventana TCP — diferencia clave entre tráfico legítimo y DDoS), `Flow_Duration`, y las tasas de paquetes/bytes por segundo.

### 4.3 Quality Gate (elemento MLOps central)

El quality gate exige **tres condiciones simultáneas** para aprobar el despliegue:

- **F1-macro ≥ 0.85:** Rendimiento global equilibrado entre clases
- **AUC-ROC ≥ 0.90:** Capacidad discriminativa robusta
- **Recall ataque ≥ 0.80:** Mínimo de detección de amenazas reales

Si cualquiera de las tres condiciones falla, `entrenamiento.py` lanza una excepción y el pipeline se detiene. Esto se activó durante el desarrollo cuando un modelo RandomForest baseline tenía F1=0.88 pero recall de ataque de solo 0.73 — el gate lo rechazó correctamente, bloqueando su despliegue.

### 4.4 Modelo en producción — carga desde Spaces

Los archivos `.pkl` no se incluyen en la imagen Docker (son demasiado grandes y cambian con cada reentrenamiento). En su lugar, `docker/entrypoint.sh` los descarga de DigitalOcean Spaces al arrancar el contenedor:

```bash
aws s3 cp "s3://${SPACES_MODELS_BUCKET}/latest/ids_model.pkl" ...
  --endpoint-url "https://${DO_REGION}.digitaloceanspaces.com"
```

Esto desacopla el ciclo de vida del modelo del ciclo de vida de la imagen Docker: se puede reentrenar y subir un nuevo modelo sin reconstruir la imagen.

---

## 5. CI/CD y Automatización

### 5.1 Pipeline unificado

Todo el CI/CD está definido en un único workflow (`ci.yml`) con cuatro jobs encadenados. El trigger es un `git push` a `main`:

```
push a main ──► lint-and-test ──► build-and-push ──► terraform ──► deploy
PR a main   ──► lint-and-test  (solo tests, sin despliegue)
```

| Job | Trigger | Tiempo estimado | Qué hace |
|-----|---------|----------------|---------|
| `lint-and-test` | push y PR | ~2 min | flake8 + pytest ≥ 70% cobertura |
| `build-and-push` | solo push | ~3 min | Build Docker + push a DOCR |
| `terraform` | solo push | ~1 min | `terraform apply` — reconcilia infraestructura |
| `deploy` | solo push | ~2 min | rsync + SSH + docker compose up + health check |

### 5.2 Autenticación con el Container Registry

La autenticación al DOCR desde GitHub Actions usa `docker/login-action` con el token de DigitalOcean como usuario y contraseña (el formato estándar de DOCR):

```yaml
- uses: docker/login-action@v3
  with:
    registry: registry.digitalocean.com
    username: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
    password: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

### 5.3 Cobertura de tests

32 tests en total. Los tests marcados como `modelo_real` se saltan en CI (requieren los `.pkl`) y se ejecutan completos en local o en el Droplet.

| Módulo | Cobertura |
|--------|----------|
| `src/data/preprocesamiento.py` | 93% |
| `src/models/evaluacion.py` | 100% |
| `src/api/schemas.py` | 100% |
| `src/features/feature_engineering.py` | 85% |
| `src/api/app.py` | 65% |
| **Total** | **88%** |

`ingesta.py` y `entrenamiento.py` se excluyen de la medición de cobertura en CI (requieren el CSV de 73 MB para ejecutarse); se validan en el ML pipeline separado.

---

## 6. Infraestructura como Código

### 6.1 Recursos Terraform sobre DigitalOcean

Terraform gestiona los recursos de forma declarativa. El Droplet **no** es creado por Terraform — se referencia como `data source` porque ya existía con otros servicios (nginx, portfolio). Terraform solo gestiona lo que NetShield necesita.

| Recurso | Nombre | Descripción |
|---------|--------|-------------|
| `digitalocean_container_registry` | `netshield-pndng` | Almacén de imágenes Docker |
| `digitalocean_spaces_bucket` | `netshield-pndng-data-dev` | Datos raw y procesados |
| `digitalocean_spaces_bucket` | `netshield-pndng-models-dev` | Modelos `.pkl` con versionado |
| `digitalocean_firewall` | `netshield-pndng-dev` | Reglas de entrada: 22, 80, 443, 8000, 5000 |
| `digitalocean_monitor_alert` (×3) | — | Email si CPU>85%, Memoria>90%, Disco>80% |

El estado de Terraform se almacena en `netshield-tf-state` (DO Spaces), configurado como backend S3-compatible:

```hcl
backend "s3" {
  bucket           = "netshield-tf-state"
  key              = "prod/terraform.tfstate"
  region           = "us-east-1"          # valor requerido por el provider S3, ignorado por Spaces
  use_path_style   = true
  skip_credentials_validation = true
  # ... flags para evitar llamadas a AWS STS/IAM
}
```

### 6.2 Decisión de diseño: Droplet como data source

Usar `data "digitalocean_droplet"` en lugar de `resource` permite que Terraform aplique cambios de firewall, registry y alertas sin riesgo de recrear (y por tanto borrar) el servidor. Este patrón es correcto cuando la infraestructura base existe fuera del ciclo de vida del proyecto.

### 6.3 Coste estimado (dev/producción en Droplet compartido)

| Recurso | Coste mensual |
|---------|--------------|
| Droplet s-1vcpu-2gb (compartido con otros servicios) | ~12 €/mes |
| Spaces (3 buckets, ~74 MB) | ~0.05 €/mes |
| Container Registry basic | ~5 €/mes |
| **Total atribuible a NetShield** | **~17 €/mes** |

---

## 7. Monitoreo y Observabilidad

Cada predicción genera un log estructurado con: hash del flujo (anonimizado), clasificación, probabilidad, nivel de amenaza y latencia. Esto permite auditoría sin almacenar datos sensibles de tráfico.

| Mecanismo | Descripción |
|-----------|-------------|
| `GET /metrics` | Contadores en tiempo real: predicciones, ataques por nivel, latencia p95 |
| Logs estructurados | Cada predicción registra `hash`, `es_ataque`, `proba`, `nivel`, `latencia_ms` |
| DO Monitor Alerts | Email automático si CPU >85%, Memoria >90% o Disco >80% |
| MLflow UI | Historial de experimentos en `http://<IP>:5000` |
| Health check Docker | `curl /health` cada 30 s; reinicio automático tras 3 fallos |

---

## 8. Metodología

### 8.1 SCRUM adaptado a trabajo individual

Framework SCRUM con sprints semanales. El Daily Standup oral se sustituyó por un Daily Log escrito (qué hice, qué haré, qué me bloquea). Los Sprint Goals fueron el elemento más valioso para mantener el foco y evitar dispersión entre tareas de modelo, API e infraestructura.

| Sprint | Objetivo | Puntos | Completado |
|--------|----------|--------|-----------|
| Sprint 1 | Pipeline datos + modelo entrenado con MLflow | 29 | 24 (83%) |
| Sprint 2 | API REST + CI + Terraform | 28 | 28 (100%) |
| Sprint 3 | CD + despliegue en Droplet + documentación | 16 | 16 (100%) |
| **Total** | | **73** | **68 (93%)** |

### 8.2 Desarrollo por especificaciones

El proyecto aplicó desarrollo por especificaciones en tres niveles distintos: definir primero el contrato o criterio de aceptación y luego implementar.

**1. Quality gate como especificación del modelo**

Antes de entrenar, se definieron explícitamente los umbrales mínimos que cualquier modelo debe cumplir para ser desplegado (F1≥0.85, AUC≥0.90, Recall≥0.80). El entrenamiento solo es exitoso si los supera. Esto invierte el flujo habitual: la especificación de calidad precede a la implementación.

**2. Schemas Pydantic como especificación de la API**

`schemas.py` define `FlowInput` y `DetectionOutput` con todos sus campos, tipos y validaciones antes de implementar los endpoints. El contrato de la API (qué acepta, qué devuelve, qué es válido) queda formalizado independientemente de la lógica de inferencia.

**3. Tests con mocks como especificación del comportamiento**

La clase `TestApiPredicciones` en `tests/test_predicciones_modelo.py` define el comportamiento esperado de la API (niveles CRITICO/ALTO/MEDIO/BAJO según probabilidad) usando mocks del modelo, sin necesidad de los `.pkl`. Esto permite que CI valide el comportamiento en cada push aunque los artefactos de entrenamiento no estén disponibles en el runner. Los tests de modelo real (`TestModeloReal`, marcados como `modelo_real`) se ejecutan solo cuando los `.pkl` existen.

---

## 9. Problemas Reales Encontrados y Soluciones

El desarrollo produjo varios problemas no documentados en tutoriales que ilustran la complejidad real de un sistema MLOps:

| Problema | Causa | Solución |
|----------|-------|---------|
| `unauthorized` en docker push | Token fine-grained sin scope `registry:write` | Generar token de acceso completo; usar `docker/login-action` |
| `BucketAlreadyExists` en Terraform | Nombres de bucket globales en DO Spaces | Añadir prefijo único `netshield-pndng-` a todos los buckets |
| Backend Terraform cambiado | `endpoint` renombrado a `endpoints` en provider v2 | Mover configuración del endpoint a `-backend-config` en CI |
| Modelo siempre devuelve 0.0 | `.pkl` gitignoreado, no incluido en imagen Docker | Entrypoint descarga modelo de Spaces al arrancar |
| DDoS clasificado como benigno en tests | Valores de tráfico DDoS erróneos (asumidos como ráfagas) | Extraer valores reales de `cicids_processed.csv` — el DDoS LOIC-UDP es lento y largo |
| `curl: not found` en healthcheck | `python:3.11-slim` no incluye curl | `apt-get install curl` en Dockerfile |
| Puerto 443 bloqueado | Firewall Terraform solo abría 22, 8000, 5000 | Añadir reglas para puertos 80 y 443 |
| `YAML: heredoc syntax error` | `<<EOF` en `script: |` rompe el parser YAML | Sustituir heredoc por `printf` en el step de deploy |

---

## 11. Conclusiones y Trabajo Futuro

### Conclusiones

1. Un pipeline MLOps con quality gate de triple umbral garantiza que solo modelos que cumplen los requisitos de ciberseguridad llegan a producción, automatizando la decisión de go/no-go.

2. La selección de 14 features (de 78) redujo la latencia de ~45 ms a ~18 ms sin pérdida significativa de rendimiento, demostrando que más features no siempre es mejor.

3. Desacoplar el ciclo de vida del modelo del de la imagen Docker (descarga desde Spaces en el entrypoint) permite reentrenar y desplegar nuevos modelos sin reconstruir la imagen — el único artefacto inmutable es el contenedor.

4. Reutilizar infraestructura existente (Droplet con otros servicios) mediante `data source` en Terraform evita recreaciones destructivas y reduce costes, a cambio de aceptar que Terraform no gestiona el ciclo de vida completo del servidor.

### Trabajo futuro

- Detección de data drift con Evidently AI para detectar cambios en los patrones de tráfico
- Clasificación multi-clase (tipo de ataque: DDoS, Brute Force, Web Attack, etc.)
- Integración con SIEM (Wazuh/ELK) para correlación de alertas
- Reentrenamiento automático semanal con nuevos datos capturados en el Droplet

---

## 12. Bibliografía

- Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization. *ICISSP 2018*.
- Sculley, D. et al. (2015). Hidden Technical Debt in Machine Learning Systems. *NIPS 2015*.
- Kim, G., Humble, J., Debois, P. y Willis, J. (2021). *The DevOps Handbook*. IT Revolution Press.
- Check Point Research (2024). Cyber Attack Trends: 2024 Mid-Year Report.
- IBM Security (2024). Cost of a Data Breach Report 2024.
- Dataset CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
- Documentación XGBoost: https://xgboost.readthedocs.io/
- Documentación FastAPI: https://fastapi.tiangolo.com/
- Documentación MLflow: https://mlflow.org/docs/latest/
- Documentación Terraform DigitalOcean Provider: https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs
