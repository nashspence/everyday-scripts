from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import wave
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared import compose


def make_wav(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fr = 44100
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fr)
        for i in range(fr):
            val = int(32767 * math.sin(2 * math.pi * 440 * i / fr))
            w.writeframes(val.to_bytes(2, "little", signed=True))


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_container_happy_path() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    inp = workdir / "input" / "tone.wav"
    out_json = workdir / "output" / "metrics.json"
    log = workdir / "output" / "loudness.log"
    make_wav(inp)
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "analyse_loudness",
            "--logfile",
            "/output/loudness.log",
            "--in-file",
            "/input/tone.wav",
            "--out-json",
            "/output/metrics.json",
            capture_output=True,
        )
        assert proc.returncode == 0
        data = json.loads(out_json.read_text())
        for key in (
            "input_i",
            "input_tp",
            "input_lra",
            "input_thresh",
            "target_offset",
        ):
            assert key in data
        log_txt = log.read_text()
        assert "Command:" in log_txt
        assert "Metrics saved" in log_txt
    finally:
        inp.unlink(missing_ok=True)
        out_json.unlink(missing_ok=True)
        log.unlink(missing_ok=True)
        compose(compose_file, workdir, "down", "-v", check=False)


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s2_missing_input() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    log = workdir / "output" / "loudness.log"
    out_json = workdir / "output" / "metrics.json"
    proc = compose(
        compose_file,
        workdir,
        "run",
        "--rm",
        "analyse_loudness",
        "--logfile",
        "/output/loudness.log",
        "--in-file",
        "/input/does_not_exist.wav",
        "--out-json",
        "/output/metrics.json",
        capture_output=True,
        check=False,
    )
    assert proc.returncode != 0
    assert not out_json.exists()
    log_txt = log.read_text()
    assert (
        "No such file" in log_txt
        or "not find" in log_txt
        or "No such file or directory" in log_txt
    )


def test_s3_unwritable_out_json(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "analyse_loudness.py"
    fake_ffmpeg = tmp_path / "ffmpeg"
    metrics = Path("/proc/metrics.json")
    fake_ffmpeg.write_text(
        '#!/bin/sh\necho \'{"input_i":-20,"input_tp":-1,"input_lra":1,"input_thresh":-30,"target_offset":0}\' >&2\n'
    )
    fake_ffmpeg.chmod(0o755)
    log = tmp_path / "log.txt"
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3])
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--logfile",
            str(log),
            "--in-file",
            "dummy.wav",
            "--out-json",
            str(metrics),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode != 0
    assert (
        "Permission" in proc.stderr
        or "denied" in proc.stderr
        or "No such file" in proc.stderr
    )


@pytest.mark.skipif(os.environ.get("IMAGE") is None, reason="IMAGE not available")  # type: ignore[misc]
def test_s4_invalid_numeric_target() -> None:
    workdir = Path(__file__).parent
    compose_file = workdir / "docker-compose.yml"
    inp = workdir / "input" / "tone.wav"
    make_wav(inp)
    log = workdir / "output" / "loudness.log"
    try:
        proc = compose(
            compose_file,
            workdir,
            "run",
            "--rm",
            "analyse_loudness",
            "--logfile",
            "/output/loudness.log",
            "--in-file",
            "/input/tone.wav",
            "--out-json",
            "/output/metrics.json",
            "--target-i",
            "0",
            capture_output=True,
            check=False,
        )
        assert proc.returncode != 0
        log_txt = log.read_text().lower()
        assert "invalid" in log_txt or "error" in log_txt or "out of range" in log_txt
    finally:
        inp.unlink(missing_ok=True)
        log.unlink(missing_ok=True)
        (workdir / "output" / "metrics.json").unlink(missing_ok=True)
        compose(compose_file, workdir, "down", "-v", check=False)
