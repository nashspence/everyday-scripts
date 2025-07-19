from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from shared import compose

import pytest

from scripts.burn_iso.burn_iso import _build_command


@pytest.mark.skipif(
    os.environ.get("IMAGE") is None,
    reason="IMAGE not available",
)  # type: ignore[misc]
def test_container_dry_run() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    iso = workdir / "input" / "dummy.iso"
    iso.write_bytes(b"iso")
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "burn_iso",
            "--iso-path",
            "/input/dummy.iso",
            "--dry-run",
            capture_output=True,
        )
        assert proc.returncode == 0
        assert "growisofs" in proc.stdout.decode()
    finally:
        iso.unlink()
        compose(compose_file, workdir, "down", "-v", check=False)


# Scenario 10 – Dry-run safety


def test_s10_dry_run(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "burn_iso.py"
    iso = tmp_path / "dummy.iso"
    iso.write_bytes(b"iso")
    log = tmp_path / "burn.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    dummy = fake_bin / "growisofs"
    dummy.write_text("#!/bin/sh\nexit 0")
    dummy.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--iso-path",
            str(iso),
            "--dry-run",
            "--speed",
            "4",
            "--device",
            "/dev/sr0",
            "--logfile",
            str(log),
            "--skip-verify",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0
    expected = f"growisofs -dvd-compat -speed=4 -Z /dev/sr0={iso}"
    assert expected in proc.stdout


# Scenario 4 – Missing ISO


def test_s4_missing_iso(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "burn_iso.py"
    missing = tmp_path / "nope.iso"
    log = tmp_path / "burn.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--iso-path",
            str(missing),
            "--logfile",
            str(log),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    assert "File not found" in proc.stderr


# Scenario 8 – Permission denied for logfile


def test_s8_logfile_permission_denied(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "burn_iso.py"
    iso = tmp_path / "dummy.iso"
    iso.write_bytes(b"iso")
    restricted = tmp_path / "no_write"
    restricted.mkdir()
    os.chmod(restricted, 0o500)
    log = restricted / "burn.log"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--iso-path",
            str(iso),
            "--logfile",
            str(log),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode != 0
    assert "Permission" in proc.stderr or "FileNotFoundError" in proc.stderr


# Scenario 9 – Device override


def test_s9_device_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    iso = tmp_path / "dummy.iso"
    iso.write_bytes(b"iso")
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.release", lambda: "5.0")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/growisofs")
    cmd = _build_command(iso=iso, verify=True, device="/dev/sr1", speed=None)
    assert cmd[-1] == f"/dev/sr1={iso}"


# Scenario 2 – Drive present, no disc


@pytest.mark.xfail(reason="Drive detection not implemented")  # type: ignore[misc]
def test_s2_drive_no_disc() -> None:
    pass


# Scenario 5 – Disc already written


@pytest.mark.xfail(reason="Blank disc check not implemented")  # type: ignore[misc]
def test_s5_disc_already_written() -> None:
    pass


# Scenario 6 – No optical drive


def test_s6_no_optical_drive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    iso = tmp_path / "dummy.iso"
    iso.write_bytes(b"iso")
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.release", lambda: "5.0")
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(FileNotFoundError):
        _build_command(iso=iso, verify=True, device=None, speed=None)


# Scenario 7 – Verify mismatch


@pytest.mark.xfail(reason="Verification step not implemented")  # type: ignore[misc]
def test_s7_verify_mismatch() -> None:
    pass
