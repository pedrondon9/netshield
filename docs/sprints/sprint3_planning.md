# Sprint 3 — Planning y Ejecución

**Fechas:** 06/05/2026 – 06/05/2026  
**Objetivo:** Pipeline CD completo y entregables finales.

---

## Sprint Goal

> "Al final del sprint, el CD construye la imagen Docker y la sube al Container Registry de DigitalOcean, el deploy se ejecuta automáticamente en el Droplet con cada push a main, y la documentación está lista para la presentación."

---

## Sprint Backlog

| ID | Historia de Usuario | Estimación | Estado |
|----|---------------------|-----------|--------|
| US10 | CD automático: build → DOCR → deploy Droplet | 8 | ✅ Done |
| US11 | Logs estructurados en contenedor | 5 | ✅ Done |
| US12 | DO Monitor Alerts (CPU/Memoria/Disco) | 3 | ✅ Done (en Terraform) |
| — | Memoria del proyecto | — | ✅ Done |
| — | Preparación presentación vídeo | — | ✅ Done |

---

## Tareas técnicas

### US10 — Pipeline CD (ci.yml job build-and-push + deploy)
- [x] docker/login-action con token DO como usuario y contraseña
- [x] Build imagen + push a registry.digitalocean.com/netshield-pndng/api
- [x] Tags :sha y :latest
- [x] rsync docker-compose.prod.yml al Droplet por SSH
- [x] SSH: docker compose pull + up --remove-orphans
- [x] Health check final contra /health
- [x] Entrypoint.sh descarga modelo desde Spaces al arrancar

### US11-12 — Monitoreo
- [x] Logs estructurados con flow_hash, clasificación, latencia en stdout
- [x] Endpoint /metrics con contadores en memoria
- [x] DO Monitor Alert: CPU >85% → email
- [x] DO Monitor Alert: Memoria >90% → email
- [x] DO Monitor Alert: Disco >80% → email

---

## Métricas

- **Velocidad:** 16 puntos
- **Cobertura tests final:** 88%
- **Imágenes DOCR:** tags sha + latest en registry.digitalocean.com/netshield-pndng/api
- **Tiempo total proyecto:** ~35 horas
