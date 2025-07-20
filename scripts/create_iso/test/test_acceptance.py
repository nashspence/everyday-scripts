from __future__ import annotations

import datetime
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared import compose


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_container_happy_path() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    build = workdir / "input" / "build"
    build.mkdir(parents=True, exist_ok=True)
    (build / "dummy.txt").write_text("hello")
    now = datetime.datetime.now(datetime.UTC)
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "create_iso",
            "--logfile",
            "/output/create.log",
            "--build-dir",
            "/input/build",
            "--iso-path",
            "/output/out.iso",
            capture_output=True,
        )
        assert proc.returncode == 0
        iso = workdir / "output" / "out.iso"
        assert iso.is_file()
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "--entrypoint",
            "xorriso",
            "create_iso",
            "-indev",
            "/output/out.iso",
            "-pvd_info",
            capture_output=True,
        )
        label = ""
        for line in proc.stdout.decode().splitlines():
            if "volume id" in line.lower():
                label = line.split(":", 1)[1].strip().strip("'\"")
                break
        assert label
        dt = datetime.datetime.strptime(label, "%Y%m%dT%H%M%SZ")
        assert abs((dt - now).total_seconds()) < 30
    finally:
        for p in build.glob("*"):
            p.unlink()
        iso = workdir / "output" / "out.iso"
        iso.unlink(missing_ok=True)
        (workdir / "output" / "create.log").unlink(missing_ok=True)
        compose(compose_file, workdir, "down", "-v", check=False)


def make_dummy_genisoimage(dir: Path) -> None:
    exe = dir / "genisoimage"
    exe.write_text(
        "#!/bin/sh\n"
        "iso=''\nprev=''\n"
        'for a in "$@"; do\n'
        "  if [ \"$prev\" = '-o' ]; then iso=$a; fi\n"
        "  prev=$a\n"
        "done\n"
        'echo dummy > "$iso"\n'
    )
    exe.chmod(0o755)


def run_script(
    tmp_path: Path, *args: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "create_iso.py"
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


def test_s3_label_too_long(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(tmp_path / "out.iso"),
        "--volume-label",
        "A" * 33,
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "Label too long" in proc.stderr


def test_s4_label_bad_chars(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(tmp_path / "out.iso"),
        "--volume-label",
        "BAD LABEL!",
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "illegal characters" in proc.stderr


def test_s5_nonexistent_build_dir(tmp_path: Path) -> None:
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(tmp_path / "missing"),
        "--iso-path",
        str(tmp_path / "out.iso"),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "Directory not found" in proc.stderr


def test_s6_empty_build_dir(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(tmp_path / "out.iso"),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "No input files" in proc.stderr


def test_s7_unwritable_iso_path(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    iso = Path("/proc/out.iso")
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(iso),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "Cannot write ISO" in proc.stderr or "Permission" in proc.stderr


def test_s8_iso_exists_no_force(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    iso = tmp_path / "out.iso"
    iso.write_text("existing")
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(iso),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert "File exists" in proc.stderr


def test_s9_iso_exists_with_force(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    iso = tmp_path / "out.iso"
    iso.write_text("existing")
    log = tmp_path / "log.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(iso),
        "--force",
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode == 0
    assert iso.read_text() == "dummy\n"


def test_s10_logfile_unwritable(tmp_path: Path) -> None:
    build = tmp_path / "build"
    build.mkdir()
    (build / "f.txt").write_text("x")
    log = Path("/proc/create.log")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    make_dummy_genisoimage(fake_bin)
    proc = run_script(
        tmp_path,
        "--logfile",
        str(log),
        "--build-dir",
        str(build),
        "--iso-path",
        str(tmp_path / "out.iso"),
        env_extra={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )
    assert proc.returncode != 0
    assert (
        "Permission" in proc.stderr
        or "Cannot write logfile" in proc.stderr
        or "FileNotFoundError" in proc.stderr
    )
