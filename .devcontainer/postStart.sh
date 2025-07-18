#!/bin/bash
/usr/local/bin/start-docker.sh
cd /workspace
python3 -m venv venv
./venv/bin/pip install --upgrade pip
PATH="/workspace/venv/bin:$PATH"
./venv/bin/pip install \
    black==25.1.0 \
    ruff==0.3.7 \
    mypy==1.10.0 \
    pytest==8.2.2
