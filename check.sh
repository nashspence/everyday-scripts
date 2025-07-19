#!/bin/bash
set -euo pipefail

# Run from the repository root
cd "$(dirname "$0")"

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
  source "venv/bin/activate"
elif [ -f "../venv/bin/activate" ]; then
  source "../venv/bin/activate"
fi

black --check .
ruff check .
git ls-files -z -- '*Dockerfile*' | xargs -0 hadolint
mypy --no-site-packages --explicit-package-bases scripts utils.py
pytest -q
