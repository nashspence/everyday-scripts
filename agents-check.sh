#!/bin/bash
set -e
pip install --quiet \
    black==25.1.0 \
    ruff==0.3.7 \
    mypy==1.10.0 \
    pytest==8.2.2
./check.sh
