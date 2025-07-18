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
# mypy is optional for these scripts
mypy --ignore-missing-imports --no-site-packages *.py tests || true
pytest -q
