#!/usr/bin/env python3
"""
Usage:
    burn_iso.py --logfile LOG --iso-path /path/to.iso
"""
import argparse
import subprocess
from pathlib import Path
from logging_utils import setup_logging, prepend_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--iso-path", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "burn")
    prepend_path()

    iso = Path(ns.iso_path)
    logger.info("Burning Blu‑ray (max speed, verify)…")
    subprocess.run(
        ["hdiutil", "burn", "-verbose", "-speed", "max", "-verifyburn", str(iso)],
        check=True,
    )
    logger.info("✅ Burn + verify completed")


if __name__ == "__main__":
    main()
