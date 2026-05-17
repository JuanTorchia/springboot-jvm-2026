#!/usr/bin/env python3
import argparse
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
RESULTS = ROOT / "results"
CDS = ROOT / ".lab-cds"
MVN = "mvn.cmd" if os.name == "nt" else "mvn"
CDS_ARCHIVE = f"app-cds-{os.getpid()}.jsa"


def run(command, check=True, capture=False):
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            check=False,
        )
    except FileNotFoundError:
        if check:
            raise
        return ""
    if check and result.returncode != 0:
        if capture and result.stdout:
            print(result.stdout)
        raise RuntimeError(f"Command failed: {' '.join(command)}")
    return result.stdout.strip() if capture and result.stdout else ""


def measure_seconds(command):
    start = time.perf_counter()
    run(command)
    return round(time.perf_counter() - start, 3)


def http_json(url, method="GET", body=None, timeout=10):
    data = None
    headers = {}
    if body is not None:
        data = body.encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
        return json.loads(payload) if payload else {}


def wait_postgres():
    run(["docker", "compose", "-f", str(ROOT / "compose.yaml"), "up", "-d", "postgres"])
    for _ in range(60):
        status = run(["docker", "inspect", "startup-lab-postgres", "--format", "{{json .State.Health.Status}}"], check=False, capture=True)
        if "healthy" in status:
            return
        time.sleep(1)
    raise RuntimeError("Postgres did not become healthy")


def dockerfile_froms(path):
    froms = []
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("FROM "):
            froms.append(stripped)
    return froms


def collect_environment():
    RESULTS.mkdir(exist_ok=True)
    env = {
        "os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "local_java_on_path": run(["java", "-version"], check=False, capture=True),
        "maven_version": run([MVN, "-version"], check=False, capture=True),
        "maven_local_java_note": "Maven may run with a newer local JDK; the project compiles with Maven release 21 and the measured JVM container uses Eclipse Temurin 21.",
        "measured_jvm_container_java": run(["docker", "run", "--rm", "--entrypoint", "java", "startup-lab:jvm", "-version"], check=False, capture=True),
        "docker_version": run(["docker", "version", "--format", "{{json .}}"], check=False, capture=True),
        "docker_compose_version": run(["docker", "compose", "version"], check=False, capture=True),
        "graalvm_version": run(["native-image", "--version"], check=False, capture=True) or "not installed locally; native builds use ghcr.io/graalvm/native-image-community:21 when enabled",
        "native_dockerfile_bases": dockerfile_froms("Dockerfile.native"),
        "native_image_inspect": run(["docker", "image", "inspect", "startup-lab:native", "--format", "{{json .RepoTags}} {{.Id}} {{.Size}}"], check=False, capture=True),
        "spring_boot_version": "3.5.13",
        "postgresql_version": run(["docker", "exec", "startup-lab-postgres", "postgres", "--version"], check=False, capture=True),
    }
    (RESULTS / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")


def compose_network():
    network = run(
        ["docker", "inspect", "startup-lab-postgres", "--format", "{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}"],
        capture=True,
    )
    if not network:
        raise RuntimeError("Could not detect Docker Compose network")
    return network


def parse_memory_mb(value):
    used = value.split("/")[0].strip()
    match = re.match(r"([0-9.]+)\s*([A-Za-z]+)", used)
    if not match:
        return 0
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "GiB":
        return round(number * 1024, 2)
    if unit == "MiB":
        return round(number, 2)
    if unit == "KiB":
        return round(number / 1024, 2)
    return round(number / 1024 / 1024, 2)


def image_size_mb(image):
    size = float(run(["docker", "image", "inspect", image, "--format", "{{.Size}}"], capture=True))
    return round(size / 1024 / 1024, 2)


def artifact_size_mb(mode):
    if mode == "native":
        output = run(["docker", "run", "--rm", "--entrypoint", "stat", "startup-lab:native", "-c", "%s", "/workspace/startup-lab"], check=False, capture=True)
        if output.strip().isdigit():
            return round(float(output.strip()) / 1024 / 1024, 2)
    jar = ROOT / "target" / "springboot-jvm-startup-lab-0.1.0-SNAPSHOT.jar"
    return round(jar.stat().st_size / 1024 / 1024, 2) if jar.exists() else 0


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    index = math.ceil((pct / 100) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def prepare_cds(network):
    CDS.mkdir(parents=True, exist_ok=True)
    archive = CDS / CDS_ARCHIVE
    container = "startup-lab-cds-prepare"
    run(["docker", "rm", "-f", container], check=False, capture=True)
    start = time.perf_counter()
    run([
        "docker", "run", "-d", "--name", container, "--network", network, "-p", "18089:8080",
        "-v", f"{CDS}:/cds",
        "-e", "SPRING_DATASOURCE_URL=jdbc:postgresql://startup-lab-postgres:5432/startup_lab",
        "-e", "SPRING_DATASOURCE_USERNAME=startup",
        "-e", "SPRING_DATASOURCE_PASSWORD=startup",
        "-e", f"JAVA_TOOL_OPTIONS=-XX:ArchiveClassesAtExit=/cds/{CDS_ARCHIVE}",
        "startup-lab:jvm",
    ], capture=True)
    try:
        for _ in range(180):
            try:
                if http_json("http://localhost:18089/actuator/health/readiness", timeout=2).get("status") == "UP":
                    break
            except Exception:
                pass
            time.sleep(0.5)
    finally:
        run(["docker", "stop", "-t", "10", container], check=False, capture=True)
        run(["docker", "rm", container], check=False, capture=True)
    elapsed = round(time.perf_counter() - start, 3)
    return archive.exists(), elapsed


def measure_mode(mode, image, network, run_number, build_seconds, appcds_prep_seconds, java_options, notes, warm_requests):
    container = f"startup-lab-{mode}-{run_number}"
    port = 18080 + run_number
    run(["docker", "rm", "-f", container], check=False, capture=True)
    command = [
        "docker", "run", "-d", "--name", container, "--network", network, "-p", f"{port}:8080",
        "-e", "SPRING_DATASOURCE_URL=jdbc:postgresql://startup-lab-postgres:5432/startup_lab",
        "-e", "SPRING_DATASOURCE_USERNAME=startup",
        "-e", "SPRING_DATASOURCE_PASSWORD=startup",
        "-e", f"JAVA_TOOL_OPTIONS={java_options}",
    ]
    if mode == "cds":
        command.extend(["-v", f"{CDS}:/cds"])
    command.append(image)

    start = time.perf_counter()
    run(command, capture=True)
    try:
        env_dump = run(["docker", "inspect", container, "--format", "{{range .Config.Env}}{{println .}}{{end}}"], check=False, capture=True)
        runtime_verification = f"JAVA_TOOL_OPTIONS={java_options or '<empty>'}"
        if mode == "aot-jvm":
            runtime_verification = "spring.aot.enabled=true verified in container env" if "JAVA_TOOL_OPTIONS=-Dspring.aot.enabled=true" in env_dump else "spring.aot.enabled=true NOT found in container env"
        elif mode == "cds":
            runtime_verification = f"AppCDS archive={CDS_ARCHIVE}; JAVA_TOOL_OPTIONS={java_options}"
        elif mode == "native":
            runtime_verification = "native executable container; no JVM runtime flags"

        ready = False
        for _ in range(240):
            try:
                if http_json(f"http://localhost:{port}/actuator/health/readiness", timeout=2).get("status") == "UP":
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.25)
        if not ready:
            raise RuntimeError(f"{mode} run {run_number} did not become ready")
        startup_ms = (time.perf_counter() - start) * 1000

        first_start = time.perf_counter()
        http_json(f"http://localhost:{port}/api/ping", timeout=10)
        first_ms = (time.perf_counter() - first_start) * 1000

        latencies = []
        errors = 0
        load_start = time.perf_counter()
        for _ in range(warm_requests):
            request_start = time.perf_counter()
            try:
                http_json(
                    f"http://localhost:{port}/api/work",
                    method="POST",
                    body='{"input":"senior-java-startup-lab","iterations":750}',
                    timeout=10,
                )
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                errors += 1
            latencies.append((time.perf_counter() - request_start) * 1000)
        elapsed = time.perf_counter() - load_start

        mem = parse_memory_mb(run(["docker", "stats", container, "--no-stream", "--format", "{{.MemUsage}}"], capture=True))
        successful = warm_requests - errors
        record = {
            "mode": mode,
            "run": run_number,
            "startup_time_ms": round(startup_ms, 2),
            "first_request_latency_ms": round(first_ms, 2),
            "warm_request_p50_ms": round(percentile(latencies, 50), 2),
            "warm_request_p95_ms": round(percentile(latencies, 95), 2),
            "warm_request_p99_ms": round(percentile(latencies, 99), 2),
            "rss_memory_mb": mem,
            "image_size_mb": image_size_mb(image),
            "artifact_size_mb": artifact_size_mb(mode),
            "build_time_seconds": build_seconds,
            "appcds_preparation_time_seconds": appcds_prep_seconds,
            "successful_requests_per_second": round(successful / elapsed if elapsed else 0, 2),
            "error_rate": round(errors / warm_requests if warm_requests else 0, 4),
            "compatibility_notes": notes,
            "runtime_verification": runtime_verification,
        }
        (RAW / f"{mode}-run-{run_number}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    finally:
        run(["docker", "rm", "-f", container], check=False, capture=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=["smoke", "editorial"], default="smoke")
    parser.add_argument("--runs", type=int, default=0)
    parser.add_argument("--warm-requests", type=int, default=0)
    parser.add_argument("--include-native", action="store_true")
    args = parser.parse_args()

    runs_count = args.runs or (3 if args.preset == "editorial" else 1)
    warm_requests = args.warm_requests or (120 if args.preset == "editorial" else 12)

    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.mkdir(parents=True, exist_ok=True)

    wait_postgres()
    network = compose_network()

    build_times = {}
    build_times["jvm"] = measure_seconds([MVN, "-q", "-DskipTests", "clean", "package"])
    run(["docker", "build", "-q", "-f", "Dockerfile.jvm", "-t", "startup-lab:jvm", "."], capture=True)
    build_times["cds"] = build_times["jvm"]
    cds_ready, cds_prep_seconds = prepare_cds(network)

    build_times["aot-jvm"] = measure_seconds([MVN, "-q", "-Pjvm-aot", "-DskipTests", "clean", "package"])
    run(["docker", "build", "-q", "-f", "Dockerfile.jvm", "-t", "startup-lab:aot", "."], capture=True)

    modes = [
        ("jvm", "startup-lab:jvm", 0, "", "baseline JVM jar"),
        ("aot-jvm", "startup-lab:aot", 0, "-Dspring.aot.enabled=true", "Spring Boot AOT generated code running on JVM; runtime flag spring.aot.enabled=true"),
    ]
    if cds_ready:
        modes.insert(1, ("cds", "startup-lab:jvm", cds_prep_seconds, f"-XX:SharedArchiveFile=/cds/{CDS_ARCHIVE} -Xshare:on", "dynamic AppCDS archive prepared before measured runs"))
    else:
        print("WARNING: CDS archive preparation failed; skipping cds mode", file=sys.stderr)

    if args.include_native or args.preset == "editorial":
        try:
            native_build = ["docker", "build", "-q", "-f", "Dockerfile.native", "-t", "startup-lab:native", "."]
            if args.preset == "editorial":
                native_build.insert(2, "--no-cache")
            build_times["native"] = measure_seconds(native_build)
            modes.append(("native", "startup-lab:native", 0, "", "GraalVM Native Image built in Docker"))
        except Exception as exc:
            print(f"WARNING: Native image build failed: {exc}", file=sys.stderr)

    collect_environment()

    for mode, image, appcds_prep_seconds, java_options, notes in modes:
        for run_number in range(1, runs_count + 1):
            print(f"Running {mode} run {run_number}/{runs_count}", flush=True)
            measure_mode(mode, image, network, run_number, build_times[mode], appcds_prep_seconds, java_options, notes, warm_requests)

    run([sys.executable, str(ROOT / "scripts" / "compare-results.py")])
    run([sys.executable, str(ROOT / "scripts" / "verify-results.py")])


if __name__ == "__main__":
    main()
