import py_compile
from pathlib import Path

import pytest

scripts = [p for p in Path(__file__).resolve().parents[1].glob("*.py")]


@pytest.mark.parametrize("script", scripts)
def test_scripts_compile(script: Path) -> None:
    py_compile.compile(str(script), doraise=True)
