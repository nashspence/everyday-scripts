#!/usr/bin/env python3
"""
High‑level wrapper that replicates `normalize_audio.sh`.

Usage:
    run_audio_pipeline.py [-i LUFS] [-t TP] input [output]
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path("/Volumes/Sabrent Rocket XTRM-Q 2TB")
LOG_DIR = ROOT / "logs"
DEFAULT_I, DEFAULT_TP = -16.0, -1.5


def utc_stamp(fmt: str = "%Y%m%dT%H%M%SZ") -> str:
    return datetime.utcnow().strftime(fmt)


def local_stamp(fmt: str = "%Y%m%dT%H%M%S") -> str:
    return datetime.now().strftime(fmt)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i",
        "--lufs",
        type=float,
        default=DEFAULT_I,
        help=f"Target integrated loudness (default {DEFAULT_I})",
    )
    ap.add_argument(
        "-t",
        "--tp",
        type=float,
        default=DEFAULT_TP,
        help=f"Target true peak in dBTP (default {DEFAULT_TP})",
    )
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ns = ap.parse_args()

    inp = Path(ns.input).expanduser().resolve()
    if not inp.exists():
        sys.exit(f"❌ not found: {inp}")

    if ns.output:
        out = Path(ns.output).expanduser().resolve()
    else:
        out = inp.with_name(f"{inp.stem}_R128{inp.suffix}")

    if out == inp:
        sys.exit("❌ refusing to overwrite input")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / f"Audio-Normalise-{local_stamp()}.log"
    log.touch()

    metrics = Path(tempfile.mktemp(prefix="loudnorm_", suffix=".json"))

    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env["PATH"]

    def run(cmd: list[str]) -> None:
        subprocess.run(cmd, env=env, check=True)

    # -- PASS 1 -------------------------------------------------------------
    run(
        [
            sys.executable,
            "analyse_loudness.py",
            "--logfile",
            str(log),
            "--in-file",
            str(inp),
            "--target-i",
            str(ns.lufs),
            "--target-tp",
            str(ns.tp),
            "--out-json",
            str(metrics),
        ]
    )

    # -- PASS 2 -------------------------------------------------------------
    run(
        [
            sys.executable,
            "normalize_audio.py",
            "--logfile",
            str(log),
            "--in-file",
            str(inp),
            "--out-file",
            str(out),
            "--target-i",
            str(ns.lufs),
            "--target-tp",
            str(ns.tp),
            "--analysis-json",
            str(metrics),
        ]
    )

    metrics.unlink(missing_ok=True)  # cleanup
    print(f"\n🎉  Done – normalised file saved to:\n{out}")
    print(f"\nFull log → {log}")


if __name__ == "__main__":
    main()
