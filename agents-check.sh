#!/bin/bash
set -euo pipefail
pip install --quiet \
    black==25.1.0 \
    ruff==0.3.7 \
    mypy==1.10.0 \
    pytest==8.2.2
# install hadolint
curl -Ls https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o /usr/local/bin/hadolint
chmod +x /usr/local/bin/hadolint
./check.sh
