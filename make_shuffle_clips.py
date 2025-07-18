#!/usr/bin/env python3
"""
Create key‑frame‑aligned clips that add up to `TARGET_SEC` seconds.

Usage:
  make_shuffle_clips.py --logfile LOG --tmp-dir DIR file1 file2 ...

Outputs:
  • ${TMP_DIR}/clip_list.txt  (ffmpeg concat list)
  • N temporary clips inside  TMP_DIR/clipNN.mkv
"""
from __future__ import annotations
import argparse
import math
import random
import subprocess
from pathlib import Path
from utils import setup_logging, prepend_path

TARGET_SEC = 600  # total montage length
MIN_CLIP = 2  # inclusive
MAX_CLIP = 5  # inclusive
PART_SCALE = 2  # same heuristic as your Bash: N ≈ 2*T/(MIN+MAX)


def ffprobe_dur(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logfile", required=True)
    ap.add_argument(
        "--tmp-dir",
        required=True,
        help="scratch directory (created beforehand by the orchestrator)",
    )
    ap.add_argument("files", nargs="+")
    ns = ap.parse_args()

    logger = setup_logging(ns.logfile, "shuffle-extract")
    prepend_path()
    files = [Path(f).resolve() for f in ns.files]

    # ------------------------------------------------------------------ 1 ‑ durations & prefix sums
    durations, prefix = [], [0.0]
    logger.info(f"{len(files)} source file(s) selected")
    for f in files:
        d = ffprobe_dur(f)
        durations.append(d)
        prefix.append(prefix[-1] + d)
        logger.info(f"{f.name:30s}  {d:8.2f}s")
    combined = prefix[-1]
    logger.info(f"Combined timeline: {combined:.2f}s")

    # ------------------------------------------------------------------ 2 ‑ plan clip count & lengths
    N = math.floor(PART_SCALE * TARGET_SEC / (MIN_CLIP + MAX_CLIP))
    logger.info(f"Planning ≈{N} clips (2‑pass heuristic)")

    lengths, s = [], 0
    rng = random.Random()  # seed‑able if desired
    for i in range(1, N + 1):
        if i == N:
            lengths.append(TARGET_SEC - s)
            break
        left = N - i
        rem = TARGET_SEC - s
        lo = max(MIN_CLIP, rem - left * MAX_CLIP)
        hi = min(MAX_CLIP, rem - left * MIN_CLIP)
        L = rng.randint(lo, hi)
        lengths.append(L)
        s += L
    assert sum(lengths) == TARGET_SEC

    part_dur = combined / len(lengths)
    logger.info(f"Each virtual partition ≈{part_dur:.2f}s")

    # ------------------------------------------------------------------ 3 ‑ extract
    tmp_dir = Path(ns.tmp_dir)
    clip_list = tmp_dir / "clip_list.txt"
    clip_list.write_text("", encoding="utf‑8")

    usable_total = 0.0
    for idx, L in enumerate(lengths, 1):
        part_start = (idx - 1) * part_dur
        max_off = part_dur - L
        offset = rng.random() * max_off
        global_start = part_start + offset

        # locate which source video contains this timestamp
        file_idx = next(
            j
            for j, p in enumerate(prefix[:-1])
            if prefix[j] <= global_start < prefix[j + 1]
        )
        src = files[file_idx]
        local_start = global_start - prefix[file_idx]

        out_clip = tmp_dir / f"clip{idx:03d}.mkv"
        logger.info(
            f"[{idx:03d}] {src.name:20s}  seek={local_start:7.2f}s  len={L:2d}s"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{local_start:.6f}",
                "-i",
                str(src),
                "-t",
                str(L),
                "-fflags",
                "+genpts",
                "-reset_timestamps",
                "1",
                "-video_track_timescale",
                "90000",
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(out_clip),
            ],
            check=True,
        )
        real_len = ffprobe_dur(out_clip)
        usable_total += real_len

        if usable_total > TARGET_SEC + 0.0001:  # overshoot → trim last clip
            excess = usable_total - TARGET_SEC
            new_len = real_len - excess
            if new_len < MIN_CLIP:  # drop it
                out_clip.unlink()
                break

            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{local_start:.6f}",
                    "-i",
                    str(src),
                    "-t",
                    f"{new_len:.6f}",
                    "-fflags",
                    "+genpts",
                    "-reset_timestamps",
                    "1",
                    "-video_track_timescale",
                    "90000",
                    "-c",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(out_clip),
                ],
                check=True,
            )
            usable_total = TARGET_SEC
            logger.info(f"Trimmed last clip to {new_len:.2f}s to hit exactly 600 s")
            with clip_list.open("a", encoding="utf-8") as fh:
                fh.write(f"file '{out_clip}'\n")
            break
        with clip_list.open("a", encoding="utf-8") as fh:
            fh.write(f"file '{out_clip}'\n")

    logger.info(f"Usable media total: {usable_total:.2f}s")
    logger.info("Clip list ready")


if __name__ == "__main__":
    main()
