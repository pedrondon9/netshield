# Guía de Presentación — NetShield Pipeline MLOps (Vídeo Individual)

**Asignatura:** 20GIAR — Metodologías de Desarrollo y Despliegue (VIU)  
**Formato:** Vídeo individual grabado (15-20 minutos)  
**Fecha límite:** 6 de mayo de 2026 a las 23:59  

---

## Estructura (13 diapositivas, ~17 minutos)

### DIAP 1 — Portada (0:00 – 0:30)

**Contenido:** "NetShield — Pipeline MLOps para Detección de Intrusiones en Red". Pedro Ndong. Proyecto 1 — Pipeline MLOps. 20GIAR, mayo 2026.

**Decir:** "Soy Pedro Ndong y presento NetShield, un pipeline MLOps completo que automatiza la detección de intrusiones en tráfico de red, desde el entrenamiento del modelo hasta el despliegue en producción en en los Droplet de DigitalOcean."

---

### DIAP 2 — El problema (0:30 – 2:00)

**Contenido:** El problema de negocio en lenguaje simple. Cifras: 1.636 ciberataques/semana por organización; tasa de falsos positivos >40% en SOCs; coste medio brecha 4.88M USD.

**Decir:** "Los equipos de seguridad procesan miles de alertas diarias de forma manual. Más del 40% son falsos positivos, lo que provoca fatiga de alertas y que ataques reales pasen desapercibidos. NetShield automatiza esta clasificación: analiza las características de cada flujo de red y lo clasifica como benigno o ataque en menos de 20 milisegundos."

---

### DIAP 3 — ¿Por qué MLOps? (2:00 – 3:30)

**Decir:** "Un modelo en un notebook no es un producto. Si entreno un modelo y lo copio manualmente al servidor, no hay garantía de que sea el mismo que evalué. No hay tests. No hay rollback. Y en ciberseguridad, desplegar un modelo degradado puede significar dejar pasar ataques reales. MLOps garantiza que solo modelos que superan umbrales de calidad llegan a producción, de forma automatizada y reproducible."

---

### DIAP 4 — Datos y EDA (3:30 – 5:00)

**Contenido:** Dataset CICIDS2017: 225k flujos, 78 features, subconjunto Friday DDoS. Distribución: 56.5% benigno, 43.5% ataque. Hallazgos: infinitos en Flow Bytes/s, 15% duplicados, 14 features seleccionadas de 78.

**Decir:** "El dataset CICIDS2017 es la referencia académica en detección de intrusiones. Tiene problemas reales de calidad: infinitos por divisiones por cero, un 15% de duplicados, y nombres de columnas con espacios extra. Estos problemas no son errores del dataset sino características realistas del tráfico capturado. Resolverlos correctamente fue una parte crítica del pipeline."

---

### DIAP 5 — Arquitectura (5:00 – 7:30)

**Contenido:** Diagrama con el pipeline CI/CD unificado (ci.yml, 4 jobs) y la infraestructura DigitalOcean.

**Decir:** "La arquitectura tiene tres capas. El repositorio GitHub como centro de control. Un único workflow de GitHub Actions con cuatro jobs encadenados: lint y tests, build y push al Container Registry, Terraform apply para reconciliar la infraestructura, y deploy por SSH al Droplet. Y la capa de DigitalOcean donde corre la API en un Droplet en Frankfurt con monitoreo de CPU, memoria y disco por email. El modelo no va en la imagen Docker sino que el entrypoint lo descarga de Spaces al arrancar, lo que desacopla el ciclo de vida del modelo del de la imagen."

**Pregunta anticipada — ¿Por qué XGBoost y no una red neuronal?** "Con 225.000 muestras y 14 features, XGBoost alcanza F1=0.964 sin GPU. Una red neuronal necesitaría más datos, GPU, y perdería la interpretabilidad del feature importance, que es valiosa para que el analista SOC entienda por qué un flujo fue clasificado como ataque."

---

### DIAP 6 — El quality gate (7:30 – 9:00)

**Contenido:** Triple umbral: F1≥0.85, AUC≥0.90, Recall≥0.80. Diagrama de flujo condicional. Caso real de activación.

**Decir:** "Este es el elemento MLOps más importante del proyecto. A diferencia del ejemplo del curso que usa dos umbrales, NetShield usa tres, porque en ciberseguridad el recall es crítico: si el modelo no detecta al menos el 80% de los ataques, es inaceptable. Esto no fue solo teoría: en el Sprint 1, un modelo RandomForest baseline tenía buen F1 pero recall de solo 0.73. El gate lo rechazó. Sin ese mecanismo, habría desplegado un modelo que dejaba pasar 1 de cada 4 ataques."

---

### DIAP 7 — Demo (9:00 – 11:00)

**Opciones de demo para el vídeo:**

**Opción A — Demo de la API (recomendada):**
1. Terminal: docker-compose up (mostrar logs de arranque)
2. Navegador: localhost:8000/docs (Swagger UI)
3. POST /predict con datos de flujo DDoS → resultado CRITICO
4. POST /predict con datos de flujo benigno → resultado BAJO
5. GET /health → status ok

**Opción B — Demo de CI/CD:**
1. Mostrar push al repositorio
2. GitHub Actions ejecutándose
3. Historial de runs verdes

**Consejo:** Grabar la demo antes de la presentación completa. Tener un vídeo de backup por si Docker tarda en arrancar.

---

### DIAP 8 — Resultados del modelo (11:00 – 12:30)

**Contenido:** Tabla de métricas vs objetivos. Feature importance top 5. Justificación del RobustScaler.

**Decir:** "El modelo supera todos los umbrales con margen. La feature más importante es Init_Win_bytes_forward (el tamaño de ventana TCP inicial), que es la diferencia clave entre tráfico legítimo y DDoS. Un dato interesante: reducir de 78 a 14 features bajó la latencia de 45ms a 18ms con solo 0.003 de pérdida en F1. En un IDS, esa reducción de latencia es muy valiosa."

---

### DIAP 9 — Infraestructura Terraform (12:30 – 13:30)

**Decir:** "Toda la infraestructura está definida en código sobre DigitalOcean: el Container Registry, dos buckets Spaces con versionado, las reglas de firewall y tres alertas de monitoreo. Con terraform apply se reconcilia en segundos. Una decisión de diseño importante: el Droplet no lo crea Terraform sino que lo referencia como data source, porque ya existía con otros servicios. Esto evita que terraform destroy borre el servidor. El estado de Terraform se guarda en un bucket Spaces, que es compatible con la API S3, por lo que el backend s3 de Terraform funciona sin cambios."

---

### DIAP 10 — Metodología ágil y desarrollo por especificaciones (13:30 – 15:00)

**Contenido:** 3 sprints, velocidad por sprint, desarrollo por especificaciones aplicado.

**Decir:** "Combiné SCRUM con desarrollo por especificaciones. La idea es definir primero el contrato —qué debe hacer el sistema y con qué criterios de calidad— y luego implementar. En NetShield esto aparece en tres puntos concretos: el quality gate define las métricas mínimas antes de entrenar el modelo, los schemas Pydantic definen el contrato de la API antes de implementar los endpoints, y los tests con mocks validan el comportamiento esperado de la API antes de tener el modelo real disponible. Esto permite que CI funcione sin los `.pkl`, que son artefactos de entrenamiento. Adapté SCRUM a trabajo individual sustituyendo el standup oral por un Daily Log escrito. La velocidad mejoró de 83% en Sprint 1 a 100% en Sprint 2-3."

---

### DIAP 11 — Conclusiones (15:00 – 16:30)

**Tres conclusiones + una recomendación:**

1. "El quality gate con triple umbral es el diferenciador de MLOps en ciberseguridad: se activó durante el desarrollo y evitó un despliegue con recall insuficiente."

2. "La selección de features redujo latencia de 45ms a 18ms sin pérdida significativa — más features no siempre es mejor."

3. "Desacoplar el modelo de la imagen Docker permite reentrenar y desplegar sin reconstruir el contenedor. El pipeline completo corre con un solo git push."

**Recomendación:** "Para producción real, añadiría detección de data drift con Evidently AI, porque los patrones de ataque evolucionan y el modelo necesita adaptarse."

---

### DIAP 12 — ¿Preguntas? (16:30+)

**Contenido:** Diapositiva con enlace al repositorio GitHub.

---

## Preguntas anticipadas

1. **"¿Por qué un solo workflow con cuatro jobs y no pipelines separados?"** → Los jobs encadenados en un único workflow garantizan que deploy nunca corre si los tests fallan, sin necesidad de coordinar entre workflows. El ML Pipeline sigue siendo un workflow separado porque tiene un trigger distinto (cambios en `src/` o `data/`) y un ciclo de vida independiente.

2. **"¿Si el modelo no supera los umbrales, qué pasa?"** → raise ValueError → exit code 1 → GitHub Actions marca el step como fallido → el job de deploy nunca arranca.

3. **"¿Por qué RobustScaler y no StandardScaler?"** → Los ataques DDoS generan valores extremos (miles de paquetes/segundo) que sesgarían media y desviación estándar. RobustScaler usa mediana e IQR, que son resistentes a outliers.

4. **"¿Cuánto costaría en producción?"** → El Droplet (~12€/mes) está compartido con otros servicios. Lo atribuible a NetShield son unos 17€/mes sumando el Container Registry y Spaces. Es sensiblemente más barato que ECS Fargate en AWS para cargas bajas.

5. **"¿Cómo elegiste las 14 features de las 78?"** → Combinación de importancia por RandomForest y conocimiento de dominio: las features de ventana TCP, tasas de paquetes y tiempos inter-arrival son las más discriminantes en la literatura de IDS.

6. **"¿Qué es el desarrollo por especificaciones y cómo lo aplicaste?"** → Es definir primero el contrato y los criterios de aceptación, y luego implementar. En NetShield: el quality gate define las métricas mínimas antes de entrenar, los schemas Pydantic definen el contrato de la API antes de los endpoints, y los tests con mocks validan el comportamiento esperado de la API antes de tener el modelo disponible. Esto es lo que permite que CI funcione en cada push sin necesitar los ficheros `.pkl`.
