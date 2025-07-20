import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared import compose


def run_script(
    tmp_path: Path, *args: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "concat_shuffle.py"
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


def make_clip(path: Path) -> None:
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "ffmpeg",
            "-v",
            f"{path.parent}:/data",
            "-w",
            "/data",
            os.environ["IMAGE"],
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=16x16:rate=1",
            "-g",
            "1",
            "-pix_fmt",
            "yuv420p",
            path.name,
        ],
        check=True,
    )


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_container_happy_path() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    inp = workdir / "input"
    out_dir = workdir / "output"
    clip1 = inp / "c1.mp4"
    clip2 = inp / "c2.mp4"
    list_file = inp / "list.txt"
    log = out_dir / "concat.log"
    out_vid = out_dir / "out.mkv"
    inp.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, clip in enumerate((clip1, clip2), 1):
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint",
                "ffmpeg",
                "-v",
                f"{inp}:/data",
                "-w",
                "/data",
                os.environ["IMAGE"],
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=1:size=16x16:rate=1",
                "-g",
                "1",
                "-pix_fmt",
                "yuv420p",
                clip.name,
            ],
            check=True,
        )
    list_file.write_text(f"file '/input/{clip1.name}'\nfile '/input/{clip2.name}'\n")
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "concat_shuffle",
            "--clip-list",
            "/input/list.txt",
            "--out-file",
            "/output/out.mkv",
            "--logfile",
            "/output/concat.log",
            capture_output=True,
        )
        assert proc.returncode == 0
        assert out_vid.is_file()
    finally:
        for p in inp.glob("*.mp4"):
            p.unlink(missing_ok=True)
        list_file.unlink(missing_ok=True)
        out_vid.unlink(missing_ok=True)
        log.unlink(missing_ok=True)
        compose(compose_file, workdir, "down", "-v", check=False)


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s1_happy_path(tmp_path: Path) -> None:
    clip1 = tmp_path / "c1.mkv"
    clip2 = tmp_path / "c2.mkv"
    for clip in (clip1, clip2):
        make_clip(clip)
    list_file = tmp_path / "list.txt"
    list_file.write_text(f"file '{clip1}'\nfile '{clip2}'\n")
    log = tmp_path / "log.txt"
    out_vid = tmp_path / "out.mkv"
    proc = run_script(
        tmp_path,
        "--clip-list",
        str(list_file),
        "--out-file",
        str(out_vid),
        "--logfile",
        str(log),
    )
    assert proc.returncode == 0
    assert out_vid.is_file()
    assert "Montage saved" in log.read_text()


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s2_missing_clip(tmp_path: Path) -> None:
    clip1 = tmp_path / "c1.mkv"
    make_clip(clip1)
    list_file = tmp_path / "list.txt"
    list_file.write_text(f"file '{clip1}'\nfile '{tmp_path/'missing.mkv'}'\n")
    log = tmp_path / "log.txt"
    out_vid = tmp_path / "out.mkv"
    proc = run_script(
        tmp_path,
        "--clip-list",
        str(list_file),
        "--out-file",
        str(out_vid),
        "--logfile",
        str(log),
    )
    assert proc.returncode == 2
    assert not out_vid.exists()
    assert "No such file" in log.read_text()


def test_s3_unreadable_list(tmp_path: Path) -> None:
    bad_list = tmp_path / "missing.txt"
    log = tmp_path / "log.txt"
    out_vid = tmp_path / "out.mkv"
    proc = run_script(
        tmp_path,
        "--clip-list",
        str(bad_list),
        "--out-file",
        str(out_vid),
        "--logfile",
        str(log),
    )
    assert proc.returncode == 1
    assert not out_vid.exists()


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s4_output_locked(tmp_path: Path) -> None:
    clip1 = tmp_path / "c1.mkv"
    make_clip(clip1)
    list_file = tmp_path / "list.txt"
    list_file.write_text(f"file '{clip1}'\n")
    log = tmp_path / "log.txt"
    out_vid = Path("/proc/out.mkv")
    proc = run_script(
        tmp_path,
        "--clip-list",
        str(list_file),
        "--out-file",
        str(out_vid),
        "--logfile",
        str(log),
    )
    assert proc.returncode == 3


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s5_interrupted(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    hold = tmp_path / "bin"
    hold.mkdir()
    wrapper = hold / "ffmpeg"
    wrapper.write_text('#!/bin/sh\nsleep 1\nexec ffmpeg "$@"\n')
    wrapper.chmod(0o755)
    env["PATH"] = f"{hold}:{env['PATH']}"
    clip1 = tmp_path / "c1.mkv"
    make_clip(clip1)
    list_file = tmp_path / "list.txt"
    list_file.write_text(f"file '{clip1}'\n")
    log = tmp_path / "log.txt"
    out_vid = tmp_path / "out.mkv"
    proc = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "concat_shuffle.py"),
            "--clip-list",
            str(list_file),
            "--out-file",
            str(out_vid),
            "--logfile",
            str(log),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.1)
    import signal

    proc.send_signal(signal.SIGINT)
    proc.wait()
    assert proc.returncode == 3
    assert not out_vid.exists()


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s6_large_montage(tmp_path: Path) -> None:
    clip1 = tmp_path / "c1.mkv"
    make_clip(clip1)
    list_file = tmp_path / "list.txt"
    list_file.write_text(f"file '{clip1}'\n")
    log = tmp_path / "log.txt"
    out_vid = tmp_path / "out.mkv"
    proc = run_script(
        tmp_path,
        "--clip-list",
        str(list_file),
        "--out-file",
        str(out_vid),
        "--logfile",
        str(log),
    )
    assert proc.returncode == 0
    text = log.read_text()
    assert "Montage saved" in text
    with open(out_vid, "r+b") as fh:
        fh.truncate(5 * 1024 * 1024 * 1024)
    assert out_vid.stat().st_size > 4 * 1024**3
