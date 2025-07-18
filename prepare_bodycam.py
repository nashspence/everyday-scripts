#!/usr/bin/env python3
"""
Usage:
    prepare_bodycam.py --logfile LOG --build-dir DIR FILE [FILE ...]
Outputs:
    - Populates DIR with either original clips or AV1‑re‑encoded versions.
    - Prints nothing; errors raise.
"""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
from pathlib import Path
from logging_utils import setup_logging, prepend_path

DISC_BYTES = 25_000_000_000  # target BD‑R size
SAFETY_BYTES = 500 * 1024 * 1024  # keep ~500 MiB free
ALLOW_BYTES = DISC_BYTES - SAFETY_BYTES


def get_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("files", nargs="+")
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "prepare")
    prepend_path()

    files = [Path(f) for f in ns.files]
    if not files:
        logger.error("❌ No input files.")
        sys.exit(1)

    build_dir = Path(ns.build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Working dir: {build_dir}")

    total_input = sum(f.stat().st_size for f in files)
    mode = "copy" if total_input <= ALLOW_BYTES else "reencode"
    logger.info(f"Disc‑fit decision: {mode.upper()}")

    if mode == "copy":
        for src in files:
            dst = build_dir / src.name
            shutil.copy2(src, dst, follow_symlinks=True)
    else:
        total_seconds = sum(get_duration(f) for f in files)
        global_kbps = math.floor((ALLOW_BYTES * 8) / 1000 / total_seconds)
        logger.info(f"Re‑encoding all clips at ~{global_kbps} kbps")

        for idx, src in enumerate(files, 1):
            base = src.stem
            out = build_dir / f"{base}_recompressed_av1.mp4"
            logger.info(f"[{idx}/{len(files)}] → {out.name}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "warning",
                    "-stats",
                    "-y",
                    "-i",
                    str(src),
                    "-map",
                    "0:v:0",
                    "-map",
                    "0:a:0",
                    "-c:v",
                    "libsvtav1",
                    "-b:v",
                    f"{global_kbps}k",
                    "-svtav1-params",
                    "rc=1",
                    "-preset",
                    "5",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "28k",
                    "-vbr",
                    "on",
                    "-compression_level",
                    "10",
                    "-application",
                    "audio",
                    "-frame_duration",
                    "40",
                    "-ar",
                    "24000",
                    "-ac",
                    "1",
                    "-cutoff",
                    "12000",
                    "-c:s",
                    "copy",
                    "-c:d",
                    "copy",
                    str(out),
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
