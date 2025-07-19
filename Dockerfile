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

# Install pytest so acceptance tests can run inside this image
RUN pip install --no-cache-dir pytest==8.2.2

WORKDIR /workspace
COPY scripts ./scripts
COPY utils.py ./utils.py
ENTRYPOINT ["python3"]
