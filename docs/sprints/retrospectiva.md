# Sprint Retrospective — Sprint 3 (y Global del Proyecto)

**Fecha:** 05/05/2026  
**Participante:** Pedro Ndong (trabajo individual)  
**Formato:** Start / Stop / Continue

---

## ¿Qué fue bien? (Continue)

- **El quality gate con triple umbral (F1 + AUC + Recall) funcionó como se diseñó.** Durante el Sprint 1, al experimentar con un RandomForest como baseline, el recall de la clase ataque bajó a 0.73. El gate lo detectó y el script falló antes de guardar el modelo. Sin ese mecanismo, habría desplegado un modelo que dejaba pasar 1 de cada 4 ataques.

- **La selección de 14 features en lugar de las 78 originales** redujo la latencia de inferencia de ~45ms a ~8ms sin pérdida significativa de rendimiento (F1 bajó solo 0.003). Esto es crítico para un IDS que necesita operar en tiempo real.

- **Docker Compose para desarrollo local** permitió tener API + MLflow reproducibles desde el primer día. La configuración del scaler como artefacto separado (scaler.pkl) evitó problemas de escalado en producción.

- **Trabajar con ramas feature y hacer self-review** antes de mergear. Aunque trabajo solo, la disciplina de revisar mi propio PR antes de merge detectó 1 bug (FEATURE_MAP con nombre incorrecto de columna).

---

## ¿Qué no funcionó? (Stop)

- **Subestimar el tamaño del dataset CICIDS2017.** El CSV completo pesa 6 GB. Tardé medio día en descargarlo y procesarlo la primera vez. Solución: usar solo el subconjunto Friday-WorkingHours (~225k filas) que es representativo de ataques DDoS.

- **No configurar .gitignore desde el inicio.** Accidentalmente commiteé el CSV al repositorio en el Sprint 1. Tuve que usar git filter-branch para limpiarlo. Lección aprendida: data/raw/ en .gitignore desde el día cero.

- **Autenticación al Container Registry de DigitalOcean desde GitHub Actions.** El token fine-grained no tenía el scope `registry:write` activo, lo que causó tres fallos consecutivos con `unauthorized` antes de identificar la causa. Lección: verificar los scopes del token antes de configurar el secreto, y usar un token de acceso completo en entornos de CI donde no se requiere restricción granular.

---

## ¿Qué mejoraríamos? (Start)

- **Pre-commit hooks** con detect-secrets para no commitear credenciales por error, y check-added-large-files para el CSV.

- **Detección de data drift con Evidently AI** para monitorizar si la distribución del tráfico en producción diverge del dataset de entrenamiento.

- **A/B testing** desplegando dos versiones del modelo y dirigiendo 10% del tráfico a la versión nueva antes de promoverla.

- **Dashboard Streamlit** para el equipo SOC que visualice las detecciones en tiempo real con gráficos de distribución.

---

## Reflexión sobre la metodología ágil

**¿Sirvió SCRUM para un proyecto individual?**

Sí, con adaptaciones. No tiene sentido hacer Daily Standups conmigo mismo, pero el Daily Log escrito cumplió la misma función: al anotar cada día qué hice, qué haré y qué me bloquea, detecté rápidamente el problema de los infinitos en CICIDS2017 (día 2) en lugar de arrastrarlo.

Los Sprint Goals fueron el elemento más valioso: tener un objetivo claro cada semana evitó que me dispersara entre optimización del modelo, documentación y configuración de infraestructura al mismo tiempo.

**¿Qué añadiría con más tiempo?**

- Un sprint dedicado a reentrenamiento automático con datos nuevos (CICIDS2018)
- Clasificación multi-clase (no solo benigno/ataque sino tipo de ataque: DDoS, Brute Force, etc.)
- Integración con un SIEM real (Wazuh o ELK Stack)

---

## Velocidad por sprint

| Sprint | Planificados | Completados | % |
|--------|-------------|-------------|---|
| Sprint 1 | 29 | 24 | 83% |
| Sprint 2 | 28 | 28 | 100% |
| Sprint 3 | 16 | 16 | 100% |
| **Total** | **73** | **68** | **93%** |
