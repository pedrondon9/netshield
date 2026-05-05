# Sprint 1 — Planning y Ejecución

**Fechas:** 05/05/2026 – 05/05/2026  
**Objetivo:** Pipeline de datos funcional y primer modelo entrenado con tracking en MLflow.

---

## Sprint Goal

> "Al final del sprint, puedo ejecutar el pipeline completo desde la ingesta del CICIDS2017 hasta el entrenamiento del modelo XGBoost, con resultados registrados en MLflow."

---

## Sprint Backlog

| ID | Historia de Usuario | Estimación | Estado |
|----|---------------------|-----------|--------|
| US01 | Carga automática CICIDS2017 | 3 | ✅ Done |
| US02 | Validación esquema/completitud/tipos | 5 | ✅ Done |
| US03 | Preprocesamiento reproducible | 8 | ✅ Done |
| US04 | Entrenamiento XGBoost + MLflow | 8 | ✅ Done |
| US14 | Feature engineering + RobustScaler | 5 | ✅ Done (parcial: sin EDA notebook) |

**Capacidad:** 29 puntos planificados → 24 completados

---

## Tareas técnicas

### US01 — Ingesta CICIDS2017
- [x] Crear src/data/ingesta.py con carga CSV
- [x] Limpiar nombres de columnas (CICIDS2017 tiene espacios extra)
- [x] Validar 60+ columnas esperadas

### US02 — Validación
- [x] EXPECTED_COLUMNS con columnas críticas
- [x] validar_completitud() con umbral configurable
- [x] validar_tipos() para columnas numéricas
- [x] validar_etiquetas() para verificar clases

### US03 — Preprocesamiento
- [x] limpiar_infinitos() — Flow Bytes/s y Flow Packets/s tienen inf
- [x] limpiar_negativos() — columnas de duración/longitud
- [x] imputar_nulos() con mediana
- [x] eliminar_duplicados() — ~15% del dataset
- [x] codificar_etiqueta_binaria() — BENIGN=0, Ataque=1
- [x] seleccionar_features() — 14 features más discriminantes
- [x] Tests con cobertura > 70%

### US04 — Entrenamiento + MLflow
- [x] XGBClassifier con scale_pos_weight para desbalance
- [x] MLflow experiment "netshield-ids"
- [x] Log: parámetros, métricas (AUC, F1, recall), artefactos
- [x] Modelo guardado en models/ids_model.pkl

---

## Daily Log (resumen)

| Día | Actividad | Impedimentos |
|-----|-----------|-------------|
| 15/04 | Setup entorno, ingesta.py | Problemas descargando CICIDS2017 (6 GB) |
| 16/04 | Preprocesamiento — bug infinitos | Flow Bytes/s con inf por Duration=0 |
| 17/04 | Preprocesamiento completo + tests | — |
| 18/04 | Feature selection + RobustScaler | Decisión: 14 features vs 78 |
| 19/04 | Entrenamiento XGBoost | — |
| 21/04 | MLflow integrado, tests OK | — |

---

## Sprint Review

**Demostrado:**
1. Ingesta y validación del CICIDS2017 en terminal
2. Preprocesamiento: 225k filas → ~190k tras limpieza
3. MLflow UI con experimento registrado (F1-macro: 0.964, AUC: 0.991)
4. Tests pasando con 76% de cobertura

**No completado:** Notebook EDA (US14 parcial — solo feature selection hecho)

---

## Métricas

- **Velocidad:** 24 puntos
- **Bugs encontrados:** 2 (infinitos en Flow Bytes/s, duplicados ~15%)
- **Cobertura tests:** 76%
- **F1-macro obtenido:** 0.964 ✅ (objetivo: ≥ 0.85)
