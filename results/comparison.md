# JVM Startup Lab Results

These numbers are local, reproducible measurements for this repository and machine. They are not universal claims.

| Mode | Runs | Startup ms | First request ms | Warm p50 ms | Warm p95 ms | Warm p99 ms | RSS MB | Image MB | Artifact MB | Build s | AppCDS prep s | Short loop req/s | Error rate | Notes | Runtime verification |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| aot-jvm | 3 | 7507.04 | 29.82 | 7.96 | 28.67 | 35.18 | 247 | 121 | 29.82 | 24.69 | 0 | 77.94 | 0 | Spring Boot AOT generated code running on JVM; runtime flag spring.aot.enabled=true | spring.aot.enabled=true verified in container env |
| cds | 3 | 8688.85 | 34.84 | 9.09 | 26.57 | 33.73 | 325.97 | 120.74 | 29.82 | 10.44 | 12.13 | 76.84 | 0 | dynamic AppCDS archive prepared before measured runs | AppCDS archive=app-cds-328744.jsa; JAVA_TOOL_OPTIONS=-XX:SharedArchiveFile=/cds/app-cds-328744.jsa -Xshare:on |
| jvm | 3 | 9842.06 | 52.22 | 10.40 | 31.55 | 50.12 | 258.50 | 120.74 | 29.82 | 10.44 | 0 | 65.53 | 0 | baseline JVM jar | JAVA_TOOL_OPTIONS=<empty> |
| native | 3 | 1434.87 | 10.45 | 5.17 | 26.26 | 30.09 | 67.68 | 65.49 | 107.45 | 573.82 | 0 | 107.77 | 0 | GraalVM Native Image built in Docker | native executable container; no JVM runtime flags |

Methodology: each row aggregates raw JSON runs from `results/raw`. Startup is measured until readiness, first request is measured after readiness, warm latency uses a separate short sequential request loop, and build time is recorded separately. The short loop request rate is only an observed smoke-comparison rate, not a throughput benchmark.
