#!/usr/bin/env python3
"""
Usage:
    run_pipeline.py FILE [FILE ...]
Creates a per‑run timestamp, log file, working dir, ISO name, and then runs:
    1. prepare_bodycam.py
    2. create_iso.py
    3. burn_iso.py
    4. utils.cleanup
All stderr/stdout from sub‑scripts is appended to the same log.
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from utils import cleanup, setup_logging

ROOT = Path("/Volumes/Sabrent Rocket XTRM-Q 2TB")
LOG_DIR = ROOT / "logs"
IMG_DIR = ROOT / "images"


def utc_ts(fmt: str) -> str:
    return datetime.datetime.utcnow().strftime(fmt)


def local_ts(fmt: str) -> str:
    return datetime.datetime.now().strftime(fmt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ns = ap.parse_args()
    files = [Path(f) for f in ns.files]

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_ts = local_ts("%Y%m%dT%H%M%S")
    logfile = LOG_DIR / f"BodyCam-Reencode-{log_ts}.log"
    logfile.touch()

    # Build dir & ISO path
    build_dir_str = tempfile.mkdtemp(
        prefix=f"bodycam_{log_ts}_",
        dir=str(IMG_DIR),
    )
    build_dir = Path(build_dir_str)
    iso_ts = utc_ts("%Y%m%dT%H%M%SZ")
    iso_path = IMG_DIR / f"{iso_ts}.iso"

    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env["PATH"]

    scripts_root = Path(__file__).resolve().parents[1]

    def run(script_name: str, *extra: str) -> None:
        script_path = scripts_root / script_name / f"{script_name}.py"
        subprocess.run(
            [sys.executable, str(script_path), "--logfile", str(logfile), *extra],
            env=env,
            check=True,
        )

    run("prepare_bodycam", "--build-dir", str(build_dir), *map(str, files))
    run(
        "create_iso",
        "--build-dir",
        str(build_dir),
        "--iso-path",
        str(iso_path),
        "--iso-ts",
        iso_ts,
    )
    run("burn_iso", "--iso-path", str(iso_path))

    logger = setup_logging(str(logfile), "cleanup")
    cleanup(build_dir, logger)

    # Summarise for the user
    print("\n🎉  Done – ISO stored at:")
    print(iso_path)
    print(f"\nFull log → {logfile}")


if __name__ == "__main__":
    main()
