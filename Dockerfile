FROM python:3.11-slim

ARG COMMIT_SHA=unknown
ENV COMMIT_SHA=${COMMIT_SHA}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    genisoimage \
    udftools \
    xorriso \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY scripts ./scripts
COPY utils.py ./utils.py
ENTRYPOINT ["python3"]
