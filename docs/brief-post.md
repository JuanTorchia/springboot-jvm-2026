# Editorial Brief: JVM Startup Time in 2026

## Repository And Revision

- Repository: local workspace `springboot-jvm-2026`.
- GitHub repo: `https://github.com/JuanTorchia/springboot-jvm-2026`.
- Public URL: `https://github.com/JuanTorchia/springboot-jvm-2026`.
- Commit hash: use the commit pointed to by tag `editorial-final-startup-matrix`; the exact hash is reported in the publication handoff because a commit cannot contain its own final hash.
- Tag: `editorial-final-startup-matrix`.
- Lab date: 2026-05-17.
- Last editorial matrix command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-lab.ps1 -Preset editorial`.
- Last editorial matrix run: 2026-05-17 17:31-17:44 America/Buenos_Aires, after enabling `-Dspring.aot.enabled=true` for `aot-jvm`.

## What Was Measured

- Spring Boot 3.5.13 backend on Java release 21.
- Modes: classic JVM, JVM with dynamic AppCDS, Spring Boot AOT on JVM with `-Dspring.aot.enabled=true`, and optionally GraalVM Native Image.
- Backend surface: readiness, ping, JSON create/read, Bean Validation, PostgreSQL 17 through Spring Data JDBC, and a deterministic work endpoint.
- Metrics: startup, first request, warm p50/p95/p99, RSS memory, Docker image size, artifact size, build time, AppCDS preparation time, short sequential warm-loop observed request rate, error rate, compatibility notes, runtime verification.
- Environment capture: `results/environment.json`.

## What Was Not Measured

- Production traffic.
- Long-running JIT warmup over minutes or hours.
- GC behavior under sustained load.
- Tail latency under realistic concurrency.
- Kubernetes scheduling, image pull time, node coldness, or autoscaling behavior.
- CRaC restore, because the required lifecycle and OS assumptions would need a separate lab.

## Defensible Conclusions

- Startup alone is an incomplete decision metric.
- In this matrix, build time must be discussed separately from startup time.
- First request latency can differ materially from warm request latency.
- AppCDS and AOT are operationally different from native image even when they chase similar startup goals.
- AOT JVM must be interpreted only when raw results show `spring.aot.enabled=true verified in container env`.
- Docker Desktop on Windows/WSL2 affects absolute times, so the results should be framed as local and reproducible.

## Conclusions Not Supported

- "GraalVM Native always wins."
- "Spring Boot is slow."
- "These numbers represent production."
- "AOT and native are interchangeable."
- "The lowest startup time is automatically the best architecture choice."

## Claims Allowed In The Post

- In this local matrix, native image reduced startup time and RSS memory versus the JVM modes.
- In this local matrix, native image moved substantial cost into build time and produced a different operational artifact.
- In this local matrix, AOT JVM improved startup versus the classic JVM only after running with `-Dspring.aot.enabled=true`.
- AppCDS archive preparation is an operational cost separate from startup.
- First request latency and warm request latency should be discussed separately.
- The short sequential warm-loop request rate is only a smoke comparison, not capacity evidence.

## Claims Forbidden In The Post

- GraalVM Native always wins.
- Spring Boot is slow.
- These numbers represent production.
- This measures Kubernetes, autoscaling, image pull time, or production cold starts.
- The short warm-loop request rate is a throughput benchmark.
- AOT JVM and native image are equivalent.
- Three runs establish universal truth.

## Recommended Angle

Use the thesis: startup time is a trap when measured alone. The stronger article is a decision framework: compare startup, first request, warm behavior, memory, build cost, image size, and compatibility work. If native wins startup, state what it bought that with. If CDS or AOT gets close enough, explain when that lower operational cost may be the better trade.

## Senior Java Hooks

- "The first request is a separate metric, not a rounding error after readiness."
- "AOT shifts work left; the build pipeline becomes part of the runtime decision."
- "CDS is boring in the best possible way when native is too expensive operationally."
- "Native image is not a faster JAR. It is a different deployment artifact with different constraints."
- "If your benchmark cannot explain what PostgreSQL, Docker, and WSL2 did to the numbers, it is not evidence yet."

## Methodological Warnings

- Always publish raw runs, not only aggregate tables.
- Run at least three iterations per mode for the editorial dataset.
- Do not count AppCDS archive preparation as startup; report it as a separate operational cost.
- Do not count native compilation as startup.
- Keep Windows Docker Desktop results clearly labeled; rerun on native Linux before making stronger infrastructure claims.

## Reviewer Objections

- "This is not production." Correct. The repo measures a controlled backend locally and says so. Do not call it production evidence.
- "Docker Desktop distorts numbers." Correct for absolute values. The results are Windows Docker Desktop/WSL2 evidence, not native Linux truth.
- "AOT and native are not equivalent." Correct. AOT JVM keeps the JVM deployment model; native image changes the artifact and compatibility surface.
- "AppCDS prep should not count as startup." Correct. It is recorded separately as `appcds_preparation_time_seconds`.
- "The req/s is not a throughput benchmark." Correct. It is a short sequential warm-loop observed rate used as smoke comparison only.
- "Three runs are not universal truth." Correct. Three runs are enough for a reproducible editorial matrix, not broad statistical generalization.

## Current Smoke Result Interpretation

The current checked-in `results/comparison.md` was regenerated from the editorial preset with 3 runs per mode on 2026-05-17. It is suitable as local evidence, with the Windows/Docker Desktop/WSL2 caveat.

Current aggregate highlights:

- `native`: ~1435 ms startup, ~10 ms first request, ~68 MB RSS, ~574 s clean Docker build.
- `cds`: ~8689 ms startup, ~35 ms first request, ~326 MB RSS, ~10 s clean JVM build, ~12 s AppCDS preparation outside measured startup.
- `aot-jvm`: ~7507 ms startup, ~30 ms first request, ~247 MB RSS, ~25 s clean Maven AOT build. Raw runs verify `spring.aot.enabled=true` in the container environment.
- `jvm`: ~9842 ms startup, ~52 ms first request, ~259 MB RSS, ~10 s clean Maven build.

The defensible punchline for this local matrix is: Native started much faster and used far less RSS, but paid for it with a much more expensive build and a different compatibility surface. AOT JVM improved startup versus the classic JVM after enabling `spring.aot.enabled=true`. CDS carried a separate archive-preparation cost and did not beat AOT in this specific rerun, which is useful evidence against overselling any one JVM-side optimization.

Use language like "in this local matrix" and "on this machine". Avoid universal claims.
