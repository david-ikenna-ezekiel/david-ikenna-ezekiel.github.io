#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/scripts/import-youtube-catalogue.py" "$@"
python3 "$ROOT_DIR/scripts/render-youtube-catalogue.py"

