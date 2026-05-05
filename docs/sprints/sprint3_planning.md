# Sprint 3 — Planning y Ejecución

**Fechas:** 06/05/2026 – 06/05/2026  
**Objetivo:** Pipeline CD completo y entregables finales.

---

## Sprint Goal

> "Al final del sprint, el CD sube la imagen a ECR con un tag de versión, el monitoreo está activo y la documentación está lista para la presentación."

---

## Sprint Backlog

| ID | Historia de Usuario | Estimación | Estado |
|----|---------------------|-----------|--------|
| US10 | CD automático a ECR | 8 | ✅ Done |
| US11 | Logs en CloudWatch | 5 | ✅ Done |
| US12 | Alarmas CloudWatch | 3 | ✅ Done (en Terraform) |
| — | Memoria del proyecto | — | ✅ Done |
| — | Preparación presentación vídeo | — | ✅ Done |

---

## Tareas técnicas

### US10 — Pipeline CD
- [x] cd.yml: trigger en tag v*.*.*
- [x] Login ECR + build + push con docker/build-push-action
- [x] Deploy a ECS con force-new-deployment
- [x] Health check post-deploy
- [x] Probado con git tag v1.0.0

### US11-12 — Monitoreo
- [x] Logs estructurados con flow_hash, clasificación, latencia
- [x] Métrica IntrusionDetectionLatency
- [x] Métrica AtaquesDetectados para dashboard SOC
- [x] Alarma latencia p95 > 500ms
- [x] Alarma volumen ataques > 100 en 5 min (posible incidente)

---

## Métricas

- **Velocidad:** 16 puntos
- **Cobertura tests final:** 82%
- **Imágenes ECR:** 3 (v1.0.0, v1.0.1, v1.1.0)
- **Tiempo total proyecto:** ~35 horas
