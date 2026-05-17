#!/usr/bin/env python3
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "mode",
    "runs",
    "startup_time_ms",
    "first_request_latency_ms",
    "warm_request_p50_ms",
    "warm_request_p95_ms",
    "warm_request_p99_ms",
    "rss_memory_mb",
    "image_size_mb",
    "artifact_size_mb",
    "build_time_seconds",
    "appcds_preparation_time_seconds",
    "successful_requests_per_second",
    "error_rate",
    "compatibility_notes",
    "runtime_verification",
}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def main():
    comparison = ROOT / "results" / "comparison.csv"
    raw_dir = ROOT / "results" / "raw"
    if not comparison.exists():
        fail("results/comparison.csv is missing")
    if not raw_dir.exists() or not list(raw_dir.glob("*.json")):
        fail("results/raw has no JSON runs")

    with comparison.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            fail(f"comparison.csv is missing columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        fail("comparison.csv has no rows")

    for path in raw_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_COLUMNS - {"runs"} - set(data.keys())
        if missing:
            fail(f"{path.name} is missing keys: {sorted(missing)}")
        if data["error_rate"] > 0:
            fail(f"{path.name} has non-zero error_rate")
        if data["mode"] == "aot-jvm" and "spring.aot.enabled=true verified" not in data.get("runtime_verification", ""):
            fail(f"{path.name} does not verify spring.aot.enabled=true at runtime")
        if data["mode"] == "cds" and data.get("appcds_preparation_time_seconds", 0) <= 0:
            fail(f"{path.name} does not include AppCDS preparation time")

    print("Results verification OK")


if __name__ == "__main__":
    main()
