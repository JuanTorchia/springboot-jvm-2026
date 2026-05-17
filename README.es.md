# Laboratorio Spring Boot JVM Startup 2026

Articulo relacionado:

- Espanol: [Spring Boot 2026: por que medir solo startup time es una trampa](https://juanchi.dev/es/blog/spring-boot-startup-time-2026-graalvm-native-aot-cds)
- Ingles: [Spring Boot 2026: Why Measuring Only Startup Time Is a Trap](https://juanchi.dev/en/blog/spring-boot-startup-time-2026-graalvm-native-aot-cds)

Laboratorio reproducible para comparar startup y tradeoffs tempranos de runtime en distintos modos de ejecucion de Spring Boot.

El objetivo no es demostrar que un modo siempre conviene. El laboratorio separa startup, primera request, latencia caliente, memoria, tiempo de build, tiempo de preparacion AppCDS, tamano de imagen, tasa observada en un loop corto/secuencial de requests calientes y notas de compatibilidad para sostener un post tecnico sin simplificar de mas.

## Como Citar Este Experimento

- Repositorio: `https://github.com/JuanTorchia/springboot-jvm-2026`
- Tag de referencia: `editorial-final-startup-matrix`
- Resultados principales: `results/comparison.md`
- Corridas crudas: `results/raw/*.json`
- Entorno medido: `results/environment.json`

Frase recomendada: "En el tag `editorial-final-startup-matrix` de `JuanTorchia/springboot-jvm-2026`, medido localmente en Windows Docker Desktop/WSL2..."

## Que Compara

- `jvm`: `java -jar` clasico sobre Eclipse Temurin 21.
- `cds`: JVM con archivo dinamico AppCDS preparado antes de medir.
- `aot-jvm`: codigo generado por Spring Boot AOT corriendo sobre JVM con `-Dspring.aot.enabled=true`.
- `native`: GraalVM Native Image construido en Docker, habilitado en la corrida editorial.

CRaC no esta incluido. Una comparacion seria necesita lifecycle de checkpoint/restore, soporte de kernel Linux, hooks de runtime y una metodologia que no confunda restore con startup de proceso.

## Backend De Prueba

API Spring Boot 3.5 pequena pero no trivial:

- Endpoints de health/readiness con Actuator.
- `GET /api/ping`.
- `POST /api/orders` con JSON y Bean Validation.
- `GET /api/orders/{id}` con PostgreSQL 17 via Spring Data JDBC.
- `POST /api/work` con CPU deterministica y una consulta liviana a base.
- Migraciones Flyway y datos iniciales.
- Tests unitarios e integracion con Testcontainers.

## Comandos

Tests:

```bash
mvn test
```

Validar Compose:

```bash
docker compose -f compose.yaml config
```

Smoke rapido en Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-lab.ps1 -Preset smoke
```

Smoke rapido en Linux:

```bash
./scripts/run-lab.sh smoke
```

Corrida editorial en Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-lab.ps1 -Preset editorial
```

Corrida editorial en Linux:

```bash
./scripts/run-lab.sh editorial
```

Regenerar resultados desde JSON crudos:

```bash
python scripts/compare-results.py
python scripts/verify-results.py
```

## Salidas

- `results/comparison.csv`
- `results/comparison.md`
- `results/environment.json`
- `results/raw/*.json`
- `results/assets/*.svg`

`successful_requests_per_second` es una tasa observada en un loop corto y secuencial. Sirve como smoke comparativo despues del arranque; no es un benchmark serio de capacidad o throughput.

## Notas Metodologicas

- No se mezcla build time con startup time.
- No se mezcla primera request con requests calientes.
- PostgreSQL existe para activar caminos reales del framework, pero el trabajo de base es chico para que no domine la medicion.
- AppCDS registra `appcds_preparation_time_seconds` separado del startup.
- AOT JVM se ejecuta con `-Dspring.aot.enabled=true` y cada JSON crudo incluye `runtime_verification`.
- Los numeros son locales y reproducibles, no una verdad universal.
- Docker Desktop en Windows corre contenedores Linux sobre WSL2; los absolutos pueden cambiar en Ubuntu nativo.
- Este laboratorio no mide scheduling de Kubernetes, autoscaling, tiempo de pull de imagen, GC largo, warmup JIT prolongado ni trafico de produccion.
- El loop corto de requests calientes no es un benchmark de throughput o capacidad.
- `smoke` valida el pipeline. Para evidencia editorial usar `editorial`.
