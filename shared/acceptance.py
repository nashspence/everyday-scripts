from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable


def dump_logs(compose_file: Path, workdir: Path) -> None:
    """Print logs from all compose containers."""
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "logs", "--no-color"],
        cwd=workdir,
        check=False,
    )
    sys.stdout.flush()


def compose(
    compose_file: Path,
    workdir: Path,
    *args: str,
    env_file: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """Run ``docker compose`` with the given arguments."""
    cmd = ["docker", "compose"]
    env = None
    if env_file:
        cmd += ["--env-file", str(env_file)]
        env = os.environ.copy()
        for line in Path(env_file).read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            key, _, val = line.partition("=")
            env[key] = val
    cmd += ["-f", str(compose_file), *args]
    return subprocess.run(
        cmd,
        check=check,
        cwd=workdir,
        env=env,
        capture_output=capture_output,
    )


def wait_for(
    predicate: Callable[[], bool],
    *,
    timeout: int = 120,
    interval: float = 0.5,
    message: str = "condition",
) -> None:
    """Wait until ``predicate`` is true or raise ``AssertionError``."""
    deadline = time.time() + timeout
    while True:
        if predicate():
            return
        if time.time() > deadline:
            raise AssertionError(f"Timed out waiting for {message}")
        time.sleep(interval)


# Repository root directory
REPO_ROOT = Path(__file__).resolve().parents[1]


def add_repo_to_path() -> None:
    """Insert the repository root at the start of ``sys.path``."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def script_path(name: str) -> Path:
    """Return the path to ``scripts/<name>/<name>.py`` inside the repo."""
    return REPO_ROOT / "scripts" / name / f"{name}.py"


def run_script(
    script: str | Path,
    tmp_path: Path,
    *args: str,
    env_extra: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Execute ``script`` with ``args`` either locally or in ``IMAGE`` if available."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    if env_extra:
        env.update(env_extra)

    if isinstance(script, str):
        script_file = script_path(script)
    else:
        script_file = script

    image = os.environ.get("IMAGE")
    if image:
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{REPO_ROOT}:/workspace:ro",
            "-v",
            f"{tmp_path}:{tmp_path}",
            "-w",
            "/workspace",
        ]

        docker_env = {"PYTHONPATH": "/workspace"}
        if env_extra:
            docker_env.update(env_extra)

        for key, val in docker_env.items():
            cmd += ["-e", f"{key}={val}"]

        cmd += [
            "--entrypoint",
            "python3",
            image,
            str(script_file.relative_to(REPO_ROOT)),
            *args,
        ]

        return subprocess.run(cmd, capture_output=True, text=True, check=check, env=env)

    return subprocess.run(
        [sys.executable, str(script_file), *args],
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )
