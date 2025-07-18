#!/usr/bin/env python3
"""
Usage:
    cleanup.py --logfile LOG --build-dir DIR
"""
import argparse
import shutil
from pathlib import Path
from logging_utils import setup_logging


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument("--build-dir", required=True)
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "cleanup")
    tgt = Path(ns.build_dir)
    if tgt.exists():
        shutil.rmtree(tgt)
        logger.info(f"Removed {tgt}")
    else:
        logger.warning(f"Nothing to delete: {tgt}")


if __name__ == "__main__":
    main()
