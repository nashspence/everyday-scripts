#!/usr/bin/env python3
"""Burn a Blu‑ray ISO image according to :doc:`../docs/burn_iso.md`.

The implementation is intentionally minimal so automated tests can run without
touching hardware. Use ``--dry-run`` during CI runs. When executed normally the
command produced by ``growisofs`` will run on the host system.
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
from pathlib import Path

from utils import setup_logging


def _build_command(
    *, iso: Path, verify: bool, device: str | None, speed: int | None
) -> list[str]:
    if shutil.which("growisofs") is None:
        raise FileNotFoundError("growisofs not found")
    dev = device or "/dev/sr0"
    cmd = ["growisofs", "-dvd-compat"]
    if speed:
        cmd.append(f"-speed={speed}")
    cmd += ["-Z", f"{dev}={iso}"]
    return cmd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso-path", required=True)
    ap.add_argument("--logfile")
    ap.add_argument("--device")
    ap.add_argument("--speed", type=int)
    verify_grp = ap.add_mutually_exclusive_group()
    verify_grp.add_argument("--verify", dest="verify", action="store_true")
    verify_grp.add_argument("--skip-verify", dest="verify", action="store_false")
    ap.add_argument("--dry-run", action="store_true")
    ap.set_defaults(verify=True)
    ns = ap.parse_args()

    logger = (
        setup_logging(ns.logfile, "burn")
        if ns.logfile
        else setup_logging("burn_iso.log", "burn")
    )

    iso = Path(ns.iso_path)
    if not iso.is_file():
        logger.error(f"File not found: {iso}")
        raise SystemExit(1)

    cmd = _build_command(iso=iso, verify=ns.verify, device=ns.device, speed=ns.speed)
    if ns.dry_run:
        logger.info("Dry-run mode – no commands executed")
        print(" ".join(shlex.quote(part) for part in cmd))
        return

    logger.info("Running burn command…")
    subprocess.run(cmd, check=True)
    logger.info("✅ Burn completed")


if __name__ == "__main__":
    main()
