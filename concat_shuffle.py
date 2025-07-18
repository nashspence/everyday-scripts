#!/usr/bin/env python3
"""
Concatenate stream‑copied clips into the final montage.

Usage:
  concat_shuffle.py --logfile LOG --clip-list PATH --out-file OUTPUT
"""
from __future__ import annotations
import argparse
import subprocess
from utils import setup_logging, prepend_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--clip-list", required=True)
    ap.add_argument("--out-file", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "shuffle-concat")
    prepend_path()

    subprocess.run(
        [
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
        ],
        check=True,
    )
    logger.info(f"Montage saved to {ns.out_file}")


if __name__ == "__main__":
    main()
