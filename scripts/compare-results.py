#!/usr/bin/env python3
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
RESULTS = ROOT / "results"
ASSETS = RESULTS / "assets"

FIELDS = [
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
]


def percentile(values, pct):
    if not values:
        return 0
    ordered = sorted(values)
    index = math.ceil((pct / 100) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def mean(values):
    return sum(values) / len(values) if values else 0


def fmt(value):
    if isinstance(value, str):
        return value
    if abs(value - round(value)) < 0.005:
        return str(int(round(value)))
    return f"{value:.2f}"


def load_runs():
    runs = []
    for path in sorted(RAW.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            runs.append(json.load(handle))
    return runs


def summarize(runs):
    grouped = defaultdict(list)
    for run in runs:
        grouped[run["mode"]].append(run)

    rows = []
    for mode, items in sorted(grouped.items()):
        notes = sorted({item.get("compatibility_notes", "") for item in items if item.get("compatibility_notes")})
        rows.append({
            "mode": mode,
            "runs": len(items),
            "startup_time_ms": mean([x["startup_time_ms"] for x in items]),
            "first_request_latency_ms": mean([x["first_request_latency_ms"] for x in items]),
            "warm_request_p50_ms": mean([x["warm_request_p50_ms"] for x in items]),
            "warm_request_p95_ms": mean([x["warm_request_p95_ms"] for x in items]),
            "warm_request_p99_ms": mean([x["warm_request_p99_ms"] for x in items]),
            "rss_memory_mb": mean([x["rss_memory_mb"] for x in items]),
            "image_size_mb": mean([x["image_size_mb"] for x in items]),
            "artifact_size_mb": mean([x["artifact_size_mb"] for x in items]),
            "build_time_seconds": mean([x["build_time_seconds"] for x in items]),
            "appcds_preparation_time_seconds": mean([x.get("appcds_preparation_time_seconds", 0) for x in items]),
            "successful_requests_per_second": mean([x["successful_requests_per_second"] for x in items]),
            "error_rate": mean([x["error_rate"] for x in items]),
            "compatibility_notes": "; ".join(notes) if notes else "none",
            "runtime_verification": "; ".join(sorted({item.get("runtime_verification", "") for item in items if item.get("runtime_verification")})),
        })
    return rows


def write_csv(rows):
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows):
    lines = [
        "# JVM Startup Lab Results",
        "",
        "These numbers are local, reproducible measurements for this repository and machine. They are not universal claims.",
        "",
        "| Mode | Runs | Startup ms | First request ms | Warm p50 ms | Warm p95 ms | Warm p99 ms | RSS MB | Image MB | Artifact MB | Build s | AppCDS prep s | Short loop req/s | Error rate | Notes | Runtime verification |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['runs']} | {fmt(row['startup_time_ms'])} | "
            f"{fmt(row['first_request_latency_ms'])} | {fmt(row['warm_request_p50_ms'])} | "
            f"{fmt(row['warm_request_p95_ms'])} | {fmt(row['warm_request_p99_ms'])} | "
            f"{fmt(row['rss_memory_mb'])} | {fmt(row['image_size_mb'])} | "
            f"{fmt(row['artifact_size_mb'])} | {fmt(row['build_time_seconds'])} | "
            f"{fmt(row['appcds_preparation_time_seconds'])} | "
            f"{fmt(row['successful_requests_per_second'])} | {fmt(row['error_rate'])} | "
            f"{row['compatibility_notes']} | {row['runtime_verification']} |"
        )
    lines.extend([
        "",
        "Methodology: each row aggregates raw JSON runs from `results/raw`. Startup is measured until readiness, first request is measured after readiness, warm latency uses a separate short sequential request loop, and build time is recorded separately. The short loop request rate is only an observed smoke-comparison rate, not a throughput benchmark.",
    ])
    (RESULTS / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def svg_bar(rows, metric, title, filename):
    ASSETS.mkdir(parents=True, exist_ok=True)
    width, height = 860, 420
    margin_left, margin_bottom = 150, 60
    chart_width, chart_height = width - margin_left - 40, height - 90
    values = [row[metric] for row in rows]
    max_value = max(values) if values else 1
    bar_gap = 14
    bar_height = max(22, (chart_height - bar_gap * max(0, len(rows) - 1)) / max(1, len(rows)))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="36" font-family="Arial" font-size="22" font-weight="700">{title}</text>',
    ]
    for index, row in enumerate(rows):
        y = 70 + index * (bar_height + bar_gap)
        bar_width = 0 if max_value == 0 else (row[metric] / max_value) * chart_width
        parts.append(f'<text x="24" y="{y + bar_height * 0.65:.1f}" font-family="Arial" font-size="14">{row["mode"]}</text>')
        parts.append(f'<rect x="{margin_left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="#2f6f73"/>')
        parts.append(f'<text x="{margin_left + bar_width + 8:.1f}" y="{y + bar_height * 0.65:.1f}" font-family="Arial" font-size="13">{fmt(row[metric])}</text>')
    parts.append("</svg>")
    (ASSETS / filename).write_text("\n".join(parts), encoding="utf-8")


def svg_scatter(rows):
    ASSETS.mkdir(parents=True, exist_ok=True)
    width, height = 860, 500
    left, top, plot_w, plot_h = 90, 70, 720, 340
    max_build = max([r["build_time_seconds"] for r in rows] + [1])
    max_start = max([r["startup_time_ms"] for r in rows] + [1])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="36" font-family="Arial" font-size="22" font-weight="700">Build time vs startup</text>',
        f'<line x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#333"/>',
        f'<text x="{left + plot_w - 90}" y="{top + plot_h + 42}" font-family="Arial" font-size="13">Build seconds</text>',
        f'<text x="18" y="{top + 12}" font-family="Arial" font-size="13">Startup ms</text>',
    ]
    for row in rows:
        x = left + (row["build_time_seconds"] / max_build) * plot_w
        y = top + plot_h - (row["startup_time_ms"] / max_start) * plot_h
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#9a3d2f"/>')
        parts.append(f'<text x="{x + 10:.1f}" y="{y + 4:.1f}" font-family="Arial" font-size="13">{row["mode"]}</text>')
    parts.append("</svg>")
    (ASSETS / "build-time-vs-startup.svg").write_text("\n".join(parts), encoding="utf-8")


def write_assets(rows):
    svg_bar(rows, "startup_time_ms", "Startup by mode (ms)", "startup-by-mode.svg")
    svg_bar(rows, "first_request_latency_ms", "First request by mode (ms)", "first-request-by-mode.svg")
    svg_bar(rows, "rss_memory_mb", "RSS memory by mode (MB)", "memory-by-mode.svg")
    svg_scatter(rows)
    svg_bar(rows, "build_time_seconds", "Tradeoff table proxy: build time (s)", "tradeoffs-build-time.svg")


def main():
    rows = summarize(load_runs())
    write_csv(rows)
    write_markdown(rows)
    write_assets(rows)
    print(f"Wrote {RESULTS / 'comparison.csv'} and {RESULTS / 'comparison.md'}")


if __name__ == "__main__":
    main()
