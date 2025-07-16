#!/usr/bin/env python3
"""
Usage:
    create_iso.py --logfile LOG --build-dir DIR --iso-path /path/to.iso --iso-ts 20250713T220342Z
"""
import argparse, os, subprocess, sys
from pathlib import Path
from logging_utils import setup_logging, prepend_path

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--build-dir", required=True)
    ap.add_argument("--iso-path", required=True)
    ap.add_argument("--iso-ts", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "iso")
    prepend_path()

    build_dir = Path(ns.build_dir)
    iso_path = Path(ns.iso_path)
    iso_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating ISO {iso_path.name} …")
    subprocess.run(
        [
            "hdiutil", "makehybrid",
            "-udf", "-iso",
            "-udf-volume-name", ns.iso_ts,
            "-default-volume-name", ns.iso_ts,
            "-o", str(iso_path), ".",
        ],
        cwd=build_dir,
        check=True,
    )
    if not iso_path.exists():
        logger.error("❌ ISO not created.")
        sys.exit(1)
    logger.info("ISO created successfully")

if __name__ == "__main__":
    main()
