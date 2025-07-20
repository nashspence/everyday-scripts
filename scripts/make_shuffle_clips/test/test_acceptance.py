from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared import compose


def run_script(tmp_path: Path, *args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "make_shuffle_clips.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env=env,
    )


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
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=60:size=16x16:rate=1",
            str(inp),
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
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--tmp-dir",
        str(out_dir),
        str(src),
    )
    assert proc.returncode == 0
    clip_list = out_dir / "clip_list.txt"
    assert clip_list.is_file()
    text = log.read_text()
    assert "Usable media total: 600.00s" in text


def test_s3_even_coverage(tmp_path: Path) -> None:
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
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    proc = run_script(
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
    )
    log = tmp_path / "shuffle.log"
    out_dir = tmp_path / "tmp"
    out_dir.mkdir()
    proc = run_script(
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
    )
    assert proc2.returncode == 0
    combined = proc2.stdout + proc2.stderr
    assert "copy" in combined


def make_dummy_ffprobe(dir: Path, dur: float) -> None:
    exe = dir / "ffprobe"
    exe.write_text(f"#!/bin/sh\necho {dur}\n")
    exe.chmod(0o755)


def test_s5_invalid_numeric(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffprobe(fake_bin, 10)
    log = tmp_path / "log.txt"
    dummy = tmp_path / "dummy.mp4"
    dummy.write_text("x")
    proc = run_script(
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
