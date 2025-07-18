#!/usr/bin/env python3
"""
Usage:
    run_shuffle_pipeline.py clip1 clip2 ...

Creates a 10‑minute random shuffle montage on the Desktop.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from utils import cleanup, setup_logging

ROOT_DESK = Path.home() / "Desktop"
LOG_DIR = ROOT_DESK  # same place as original
PATH_ENV = "/opt/homebrew/bin:/usr/local/bin"


def timestamp(fmt: str) -> str:
    return datetime.now().strftime(fmt)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("❌  No input files")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / f"Montage-Shuffle-{timestamp('%Y%m%dT%H%M%S')}.log"
    log.touch()

    tmp_dir = Path(tempfile.mkdtemp(prefix="shuffle_", dir="/tmp"))
    clip_list = tmp_dir / "clip_list.txt"
    out_file = ROOT_DESK / f"montage_{timestamp('%Y%m%d_%H%M%S')}.mkv"

    env = os.environ.copy()
    env["PATH"] = f"{PATH_ENV}:{env['PATH']}"

    scripts_root = Path(__file__).resolve().parents[1]

    def run(cmd: list[str]) -> None:
        subprocess.run(cmd, env=env, check=True)

    # -- extract -------------------------------------------------------------
    run(
        [
            sys.executable,
            str(scripts_root / "make_shuffle_clips" / "make_shuffle_clips.py"),
            "--logfile",
            str(log),
            "--tmp-dir",
            str(tmp_dir),
            *sys.argv[1:],
        ]
    )

    # -- concat --------------------------------------------------------------
    run(
        [
            sys.executable,
            str(scripts_root / "concat_shuffle" / "concat_shuffle.py"),
            "--logfile",
            str(log),
            "--clip-list",
            str(clip_list),
            "--out-file",
            str(out_file),
        ]
    )

    # -- clean ---------------------------------------------------------------
    logger = setup_logging(str(log), "cleanup")
    cleanup(tmp_dir, logger)

    print(f"\n🎉  Shuffle montage ready:\n{out_file}")
    print(f"\nFull log → {log}")


if __name__ == "__main__":
    main()
