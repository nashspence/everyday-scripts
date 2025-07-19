#!/usr/bin/env python3
"""
Run the first loudnorm pass and save its JSON metrics.

Usage:
    analyse_loudness.py --logfile LOG --in-file IN --target-i -16 --target-tp -1.5 --out-json METRICS.json
"""
from __future__ import annotations
import argparse
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, cast
from utils import setup_logging


def extract_json(stderr: str) -> dict[str, Any]:
    """Pull the { … } block printed by FFmpeg and load it."""
    m = re.search(r"\{\s*\"input_i\".*\}", stderr, re.S)
    if not m:
        raise RuntimeError("Could not find loudnorm JSON in FFmpeg output")
    return cast(dict[str, Any], json.loads(m.group(0)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--in-file", required=True)
    ap.add_argument("--target-i", type=float, default=-16.0)
    ap.add_argument("--target-tp", type=float, default=-1.5)
    ap.add_argument("--out-json", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "loudnorm-pass1")

    logger.info(
        "PASS 1 analysing -> target %s LUFS / %s dBTP" % (ns.target_i, ns.target_tp)
    )
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "verbose",
        "-i",
        ns.in_file,
        "-af",
        f"highpass=f=120,loudnorm=I={ns.target_i}:TP={ns.target_tp}:LRA=11:print_format=json",
        "-f",
        "null",
        "-",
    ]
    logger.info("Command: %s", " ".join(shlex.quote(p) for p in cmd))
    try:
        proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        logger.error(exc.stderr.strip())
        raise SystemExit(exc.returncode)
    metrics = extract_json(proc.stderr)

    try:
        Path(ns.out_json).write_text(json.dumps(metrics, indent=2))
    except OSError as exc:  # pragma: no cover
        logger.error(str(exc))
        raise SystemExit(1)
    logger.info(f"Metrics saved to {ns.out_json}")


if __name__ == "__main__":
    main()
