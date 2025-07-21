from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from shared.acceptance import run_script

from shared import compose  # noqa: E402


def make_dummy_ffmpeg(dir: Path) -> None:
    exe = dir / "ffmpeg"
    exe.write_text(
        """#!/usr/local/bin/python3
import sys, pathlib, re
args = sys.argv[1:]
out = args[-1]
length = 1.0
for i, a in enumerate(args):
    if a == '-t' and i + 1 < len(args):
        length = float(args[i+1])
    elif 'testsrc=duration=' in a:
        m = re.search(r'duration=([0-9.]+)', a)
        if m:
            length = float(m.group(1))
pathlib.Path(out).write_text(str(length))
if '-c' in args:
    idx = args.index('-c')
    if idx + 1 < len(args) and args[idx+1] == 'copy':
        print('copy')
"""
    )
    exe.chmod(0o755)


def make_dummy_ffprobe(dir: Path, dur: float | None = None) -> None:
    exe = dir / "ffprobe"
    if dur is None:
        exe.write_text(
            """#!/usr/local/bin/python3
import sys, pathlib
print(pathlib.Path(sys.argv[-1]).read_text().strip())
"""
        )
    else:
        exe.write_text(f"#!/bin/sh\necho {dur}\n")
    exe.chmod(0o755)


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_container_custom_lengths() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    inp = workdir / "input" / "src.mp4"
    log = workdir / "output" / "shuffle.log"
    tmp = workdir / "output" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "ffmpeg",
            "-v",
            f"{workdir / 'input'}:/data",
            "-w",
            "/data",
            os.environ["IMAGE"],
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=60:size=16x16:rate=30",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            "src.mp4",
        ],
        check=True,
    )
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "make_shuffle_clips",
            "--logfile",
            "/output/shuffle.log",
            "--tmp-dir",
            "/output/tmp",
            "--target-sec",
            "5",
            "--min-clip",
            "1",
            "--max-clip",
            "2",
            "/input/src.mp4",
            capture_output=True,
        )
        assert proc.returncode == 0
        clip_list = tmp / "clip_list.txt"
        assert clip_list.is_file()
        total = 0.0
        for line in clip_list.read_text().splitlines():
            if not line.strip():
                continue
            path = Path(line.split("'", 1)[1].rstrip("'"))
            rel = path.relative_to("/output")
            out = subprocess.check_output(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--entrypoint",
                    "ffprobe",
                    "-v",
                    f"{workdir / 'output'}:/data:ro",
                    os.environ["IMAGE"],
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=nw=1:nk=1",
                    f"/data/{rel}",
                ],
                text=True,
            )
            total += float(out.strip())
        assert abs(total - 5) < 0.1
    finally:
        inp.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)
        log.unlink(missing_ok=True)
        compose(compose_file, workdir, "down", "-v", check=False)


def _ffprobe_dur(path: Path) -> float:
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


def test_s1_happy_path(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    make_dummy_ffprobe(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    src = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1000:size=16x16:rate=30",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(src),
        ],
        check=True,
        env={"PATH": env_path},
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    out_dir.chmod(0o777)
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(out_dir),
        str(src),
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 0
    clip_list = out_dir / "clip_list.txt"
    assert clip_list.is_file()
    text = log.read_text()
    assert "Usable media total: 600.00s" in text


def test_s3_even_coverage(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    make_dummy_ffprobe(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    src = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=60:size=16x16:rate=30",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(src),
        ],
        check=True,
        env={"PATH": env_path},
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    out_dir.chmod(0o777)
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(out_dir),
        "--target-sec",
        "10",
        "--min-clip",
        "1",
        "--max-clip",
        "2",
        "--seed",
        "123",
        str(src),
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 0
    part = None
    starts: list[float] = []
    lengths: list[tuple[int, float]] = []
    for line in log.read_text().splitlines():
        if "Each virtual partition" in line:
            part = float(line.split("≈", 1)[1].split("s", 1)[0])
        if "seek=" in line and "len=" in line:
            idx = int(line.split("[", 1)[1].split("]", 1)[0])
            seek = float(line.split("seek=", 1)[1].split("s", 1)[0])
            L = float(line.split("len=", 1)[1].split("s", 1)[0])
            starts.append(seek)
            lengths.append((idx, L))
    assert part is not None
    last = -1.0
    for (i, L), s in zip(lengths, starts):
        assert s > last
        assert s >= (i - 1) * part - 0.01
        assert s <= (i) * part - L + 0.01
        last = s


def test_s4_keyframe_integrity(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    make_dummy_ffprobe(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    src = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=60:size=16x16:rate=30",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            str(src),
        ],
        check=True,
        env={"PATH": env_path},
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    out_dir.chmod(0o777)
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(out_dir),
        "--target-sec",
        "6",
        "--min-clip",
        "2",
        "--max-clip",
        "2",
        "--seed",
        "4",
        str(src),
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 0
    clip_list = out_dir / "clip_list.txt"
    out_vid = tmp_path / "out.mkv"
    proc2 = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "info",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(clip_list),
            "-c",
            "copy",
            str(out_vid),
        ],
        capture_output=True,
        text=True,
        env={"PATH": env_path},
    )
    assert proc2.returncode == 0
    combined = proc2.stdout + proc2.stderr
    assert "copy" in combined


def test_s5_invalid_numeric(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffprobe(fake_bin, 10)
    log = tmp_path / "log.txt"
    dummy = tmp_path / "dummy.mp4"
    dummy.write_text("x")
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(tmp_path / "tmp"),
        "--min-clip",
        "8",
        "--max-clip",
        "5",
        str(dummy),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "MIN_CLIP" in proc.stderr


def test_s6_short_footage(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffprobe(fake_bin, 1)
    log = tmp_path / "log.txt"
    dummy = tmp_path / "dummy.mp4"
    dummy.write_text("x")
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(tmp_path / "tmp"),
        "--target-sec",
        "120",
        str(dummy),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "shorter" in proc.stderr


def test_s7_unwritable_tmp(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffprobe(fake_bin, 10)
    ro_dir = Path("/proc/no_write")
    log = tmp_path / "log.txt"
    dummy = tmp_path / "dummy.mp4"
    dummy.write_text("x")
    proc = run_script(
        "make_shuffle_clips",
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(ro_dir),
        str(dummy),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "tmp-dir" in proc.stderr or "Permission" in proc.stderr
