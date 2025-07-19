#!/usr/bin/env python3
"""
Second loudnorm pass – applies the measured values and writes the R128 file.

Usage:
    normalize_audio.py --logfile LOG --in-file IN --out-file OUT --target-i -16 --target-tp -1.5 --analysis-json METRICS.json
"""
from __future__ import annotations
import argparse
import json
import subprocess
from utils import setup_logging


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--in-file", required=True)
    ap.add_argument("--out-file", required=True)
    ap.add_argument("--target-i", type=float, default=-16.0)
    ap.add_argument("--target-tp", type=float, default=-1.5)
    ap.add_argument("--analysis-json", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "loudnorm-pass2")

    m = json.loads(open(ns.analysis_json).read())
    for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
        if k not in m or m[k] in ("", None):
            raise RuntimeError(f"Missing key in metrics: {k}")

    logger.info(f"PASS 2 normalising → {ns.out_file}")
    filter_complex = (
        "[0:a]highpass=f=120,"
        f"loudnorm=I={ns.target_i}:TP={ns.target_tp}:LRA=11:"
        f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
        f"offset={m['target_offset']}:linear=true:print_format=summary,"
        "aresample=async=1:first_pts=0[a]"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "verbose",
        "-y",
        "-i",
        ns.in_file,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v?",  # copy video if it exists
        "-map",
        "[a]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        ns.out_file,
    ]
    subprocess.run(cmd, check=True)
    logger.info("✓ done – file normalised and saved")


if __name__ == "__main__":
    main()
