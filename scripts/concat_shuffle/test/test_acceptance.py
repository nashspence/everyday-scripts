import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared import compose


def make_dummy_ffmpeg(dir: Path) -> None:
    exe = dir / "ffmpeg"
    exe.write_text(
        """#!/usr/bin/env python3
import os, sys, time, pathlib
args = sys.argv[1:]
clip_file = None
for i,a in enumerate(args):
    if a == '-i' and i+1 < len(args):
        clip_file = args[i+1]
output = args[-1]
text = ''
try:
    text = pathlib.Path(clip_file).read_text()
except Exception as exc:
    print('No such file or directory', file=sys.stderr)
    sys.exit(1)
for line in text.splitlines():
    if line.startswith('file '):
        path = line.split("'",1)[1].rstrip("'")
        if not pathlib.Path(path).exists():
            print('No such file or directory', file=sys.stderr)
            sys.exit(1)
if os.environ.get('FF_HOLD'):
    time.sleep(float(os.environ['FF_HOLD']))
try:
    with open(output, 'wb') as fh:
        if os.environ.get('FF_LARGE'):
            fh.truncate(5 * 1024 * 1024 * 1024)
        else:
            fh.write(b'done')
except Exception as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
print('copy')
""",
    )
    exe.chmod(0o755)


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
    list_file.write_text(f"file '{clip1}'\nfile '{clip2}'\n")
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


def test_s1_happy_path(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    clip1 = tmp_path / "c1.mkv"
    clip2 = tmp_path / "c2.mkv"
    clip1.write_text("a")
    clip2.write_text("b")
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
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 0
    assert out_vid.is_file()
    assert "Montage saved" in log.read_text()


def test_s2_missing_clip(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    clip1 = tmp_path / "c1.mkv"
    clip1.write_text("a")
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
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 2
    assert not out_vid.exists()
    assert "No such file" in log.read_text()


def test_s3_unreadable_list(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
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
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 1
    assert not out_vid.exists()


def test_s4_output_locked(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    clip1 = tmp_path / "c1.mkv"
    clip1.write_text("a")
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
        env_extra={"PATH": env_path},
    )
    assert proc.returncode == 3


def test_s5_interrupted(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    env["FF_HOLD"] = "2"
    clip1 = tmp_path / "c1.mkv"
    clip1.write_text("a")
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
    time.sleep(0.5)
    import signal

    proc.send_signal(signal.SIGINT)
    proc.wait()
    assert proc.returncode == 3
    assert not out_vid.exists()


def test_s6_large_montage(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_ffmpeg(fake_bin)
    env_path = f"{fake_bin}:{os.environ['PATH']}"
    clip1 = tmp_path / "c1.mkv"
    clip1.write_text("a")
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
        env_extra={"PATH": env_path, "FF_LARGE": "1"},
    )
    assert proc.returncode == 0
    assert out_vid.stat().st_size > 4 * 1024**3
