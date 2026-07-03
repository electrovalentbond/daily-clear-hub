#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
fi

echo "==> macOS/跨平台单测（不依赖 Win32）"
$PYTHON -m unittest discover -s tests -p 'test_*.py' -v
