#!/usr/bin/env python3
"""Concatenate stream‑copied clips into the final montage.

Usage:
  concat_shuffle.py --clip-list PATH --out-file OUTPUT [--logfile LOG]
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

from utils import setup_logging


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile")
    ap.add_argument("--clip-list", required=True)
    ap.add_argument("--out-file", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile or "/dev/stdout", "shuffle-concat")

    clip_list = Path(ns.clip_list)
    try:
        clip_list.read_text()
    except Exception as exc:  # pragma: no cover - argparse ensures path exists
        logger.error(str(exc))
        raise SystemExit(1)

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        ns.clip_list,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        ns.out_file,
    ]
    logger.info("Command: %s", " ".join(shlex.quote(p) for p in cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except KeyboardInterrupt:
        logger.error("Interrupted")
        Path(ns.out_file).unlink(missing_ok=True)
        raise SystemExit(3)

    if proc.returncode != 0 or "No such file or directory" in proc.stderr:
        logger.error(proc.stderr.strip())
        if (
            "No such file or directory" in proc.stderr
            and ns.out_file not in proc.stderr
        ):
            code = 2
        else:
            code = 3
        Path(ns.out_file).unlink(missing_ok=True)
        raise SystemExit(code)

    if not Path(ns.out_file).is_file() or Path(ns.out_file).stat().st_size == 0:
        logger.error("Output not created")
        raise SystemExit(3)

    logger.info(f"Montage saved to {ns.out_file}")


if __name__ == "__main__":
    main()
