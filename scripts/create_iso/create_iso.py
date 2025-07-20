#!/usr/bin/env python3
"""Create a UDF+ISO-9660 image according to :doc:`../docs/create_iso.md`."""

from __future__ import annotations

import argparse
import datetime
import re
import shutil
import subprocess
from pathlib import Path

from utils import setup_logging

LABEL_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def _build_command(*, build_dir: Path, iso_path: Path, label: str) -> list[str]:
    """Return the command used to create the ISO."""
    if shutil.which("xorriso") is None:
        raise FileNotFoundError("xorriso not found")
    return [
        "xorriso",
        "-as",
        "mkisofs",
        "-iso-level",
        "3",
        "-udf",
        "-V",
        label,
        "-o",
        str(iso_path),
        str(build_dir),
    ]


def _validate_label(label: str) -> None:
    if not LABEL_RE.fullmatch(label):
        if len(label) > 32:
            raise ValueError("Label too long")
        raise ValueError("Label contains illegal characters")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("--iso-path", required=True)
    ap.add_argument("--volume-label")
    ap.add_argument("--force", action="store_true")
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "iso")

    build_dir = Path(ns.build_dir)
    if not build_dir.is_dir():
        logger.error("Directory not found")
        raise SystemExit(1)
    if not any(build_dir.iterdir()):
        logger.error("No input files")
        raise SystemExit(1)

    iso_path = Path(ns.iso_path)
    try:
        iso_path.parent.mkdir(parents=True, exist_ok=True)
        test_file = iso_path.parent / ".write_test"
        test_file.touch()
        test_file.unlink()
    except Exception:
        logger.error("Cannot write ISO")
        raise SystemExit(1)

    if iso_path.exists() and not ns.force:
        logger.error("File exists")
        raise SystemExit(1)

    start_ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    label = ns.volume_label or start_ts
    try:
        _validate_label(label)
    except ValueError as exc:  # noqa: PERF203
        logger.error(str(exc))
        raise SystemExit(1)

    cmd = _build_command(build_dir=build_dir, iso_path=iso_path, label=label)

    logger.info("Creating ISO image…")
    subprocess.run(cmd, check=True)

    if not iso_path.is_file() or iso_path.stat().st_size == 0:
        logger.error("ISO not created")
        raise SystemExit(1)

    logger.info("ISO created successfully")


if __name__ == "__main__":  # pragma: no cover
    main()
