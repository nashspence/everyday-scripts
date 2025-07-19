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
