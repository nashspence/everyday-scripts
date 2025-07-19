FROM python:3.11-slim

ARG COMMIT_SHA=unknown
ENV COMMIT_SHA=${COMMIT_SHA}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg=7:6.1.1-3ubuntu5 \
    genisoimage=9:1.1.11-3.5 \
    dvd+rw-tools=7.1-14build2 \
    udftools=2.3-1build2 \
    xorriso=1:1.5.6-1.1ubuntu3 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /workspace
COPY scripts ./scripts
COPY utils.py ./utils.py
ENTRYPOINT ["python3"]
