#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRESET="${1:-smoke}"
shift || true

python3 "$ROOT/scripts/run-lab.py" --preset "$PRESET" "$@"
