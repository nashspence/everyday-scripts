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
import subprocess
from pathlib import Path
from logging_utils import setup_logging, prepend_path


def extract_json(stderr: str) -> dict:
    """Pull the { … } block printed by FFmpeg and load it."""
    m = re.search(r"\{\s*\"input_i\".*\}", stderr, re.S)
    if not m:
        raise RuntimeError("Could not find loudnorm JSON in FFmpeg output")
    return json.loads(m.group(0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--in-file", required=True)
    ap.add_argument("--target-i", type=float, default=-16.0)
    ap.add_argument("--target-tp", type=float, default=-1.5)
    ap.add_argument("--out-json", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "loudnorm-pass1")
    prepend_path()

    logger.info(f"PASS 1 analysing → target {ns.target_i} LUFS / {ns.target_tp} dBTP")
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
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, check=True)
    metrics = extract_json(proc.stderr)

    Path(ns.out_json).write_text(json.dumps(metrics, indent=2))
    logger.info(f"Metrics saved to {ns.out_json}")


if __name__ == "__main__":
    main()
