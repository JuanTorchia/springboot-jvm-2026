# Spring Boot JVM Startup Lab 2026

Related article:

- English: [Spring Boot 2026: Why Measuring Only Startup Time Is a Trap](https://juanchi.dev/en/blog/spring-boot-startup-time-2026-graalvm-native-aot-cds)
- Spanish: [Spring Boot 2026: por que medir solo startup time es una trampa](https://juanchi.dev/es/blog/spring-boot-startup-time-2026-graalvm-native-aot-cds)

Reproducible lab for comparing Spring Boot startup and early-runtime tradeoffs across JVM execution modes.

The goal is not to prove that one mode is always better. The lab separates startup time, first request latency, warm request latency, memory, build time, AppCDS preparation time, image size, a short sequential warm-loop observed request rate, and compatibility notes so the result can support a technical article without flattening the tradeoffs.

Spanish version: [README.es.md](README.es.md)

## How to Cite This Experiment

- Repository: `https://github.com/JuanTorchia/springboot-jvm-2026`
- Reference tag: `editorial-final-startup-matrix`
- Primary results: `results/comparison.md`
- Raw runs: `results/raw/*.json`
- Environment capture: `results/environment.json`

Recommended wording: "In the `editorial-final-startup-matrix` tag of `JuanTorchia/springboot-jvm-2026`, measured locally on Windows Docker Desktop/WSL2..."

## What This Compares

- `jvm`: classic `java -jar` on Eclipse Temurin 21.
- `cds`: JVM with a prepared dynamic AppCDS archive.
- `aot-jvm`: Spring Boot AOT generated code running on the JVM with `-Dspring.aot.enabled=true`.
- `native`: GraalVM Native Image built in Docker, enabled for editorial runs.

CRaC is intentionally not included. A credible CRaC comparison needs checkpoint/restore lifecycle handling, Linux kernel support, runtime hooks, and a methodology that does not pretend restore is the same thing as process startup.

## Test Backend

This is a small but non-trivial Spring Boot 3.5 API:

- Actuator health/readiness endpoints.
- `GET /api/ping`.
- `POST /api/orders` with JSON deserialization and Bean Validation.
- `GET /api/orders/{id}` backed by PostgreSQL 17 through Spring Data JDBC.
- `POST /api/work` with deterministic CPU work plus a lightweight database count.
- Flyway migrations and seed data.
- Unit and integration tests with Testcontainers.

## Metrics

Each measured run writes one JSON file under `results/raw/`. Aggregated outputs are generated as:

- `results/comparison.csv`
- `results/comparison.md`
- `results/environment.json`
- `results/assets/startup-by-mode.svg`
- `results/assets/first-request-by-mode.svg`
- `results/assets/memory-by-mode.svg`
- `results/assets/build-time-vs-startup.svg`
- `results/assets/tradeoffs-build-time.svg`

Recorded columns:

- `startup_time_ms`
- `first_request_latency_ms`
- `warm_request_p50_ms`
- `warm_request_p95_ms`
- `warm_request_p99_ms`
- `rss_memory_mb`
- `image_size_mb`
- `artifact_size_mb`
- `build_time_seconds`
- `appcds_preparation_time_seconds`
- `successful_requests_per_second`
- `error_rate`
- `compatibility_notes`
- `runtime_verification`

`successful_requests_per_second` is a short sequential warm-loop observed rate. It is useful as a smoke comparison that the mode can serve repeated requests after startup; it is not a capacity or throughput benchmark.

## Requirements

- Docker Desktop or Docker Engine with Compose.
- Maven 3.9+.
- Java 21+ for local Maven builds. The project compiles with `release 21`.
- Python 3.10+.

Native image builds do not require local GraalVM because `Dockerfile.native` builds inside `ghcr.io/graalvm/native-image-community:21`.

## Commands

Run tests:

```bash
mvn test
```

Validate Docker Compose:

```bash
docker compose -f compose.yaml config
```

Quick smoke run on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-lab.ps1 -Preset smoke
```

Quick smoke run on Linux:

```bash
./scripts/run-lab.sh smoke
```

Editorial run on Windows, with 3 runs per mode and native enabled:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-lab.ps1 -Preset editorial
```

Editorial run on Linux:

```bash
./scripts/run-lab.sh editorial
```

Regenerate tables and charts from raw JSON:

```bash
python scripts/compare-results.py
python scripts/verify-results.py
```

## Methodology Notes

- Build time is recorded separately from startup time.
- First request latency is recorded separately from warm request latency.
- PostgreSQL is present to exercise realistic framework paths, but the workload is intentionally small so the database does not dominate the benchmark.
- Results are local and reproducible, not universal truth.
- Docker Desktop on Windows runs Linux containers through WSL2; absolute numbers can differ from native Linux.
- This lab does not measure Kubernetes scheduling, autoscaling, image pull time, long-running GC behavior, long JIT warmup, or production traffic.
- The short warm request loop is not a throughput or capacity benchmark.
- The smoke preset is only a pipeline check. Use the editorial preset for article evidence.

## Compatibility Notes

- Spring Boot AOT starts the application during build-time processing; that cost belongs to build time, not startup time.
- AppCDS archive preparation is done before measured runs and is not counted as startup time.
- AppCDS archive preparation time is recorded separately as `appcds_preparation_time_seconds`.
- AOT JVM runs include `-Dspring.aot.enabled=true`; raw JSON includes `runtime_verification` for this flag.
- Native image compatibility should be judged from the native build logs and runtime smoke result. If native fails, keep the failure as evidence instead of silently dropping it from the article.
