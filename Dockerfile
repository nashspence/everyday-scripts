FROM python:3.11-slim

ARG COMMIT_SHA=unknown
ENV COMMIT_SHA=${COMMIT_SHA}

ENV DEBIAN_FRONTEND=noninteractive
# Pin versions to satisfy hadolint DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:5.1.6-0+deb12u1 \
    genisoimage=9:1.1.11-3.4 \
    dvd+rw-tools=7.1-14+b1 \
    udftools=2.3-1 \
    xorriso=1.5.4-4 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /workspace
COPY scripts ./scripts
COPY utils.py ./utils.py
ENTRYPOINT ["python3"]
