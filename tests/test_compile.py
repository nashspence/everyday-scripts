import py_compile
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parents[1]
scripts = [p for p in repo_root.joinpath("scripts").rglob("*.py")]
scripts.append(repo_root / "utils.py")


@pytest.mark.parametrize("script", scripts)
def test_scripts_compile(script: Path) -> None:
    py_compile.compile(str(script), doraise=True)
