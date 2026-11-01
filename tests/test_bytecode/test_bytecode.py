import py_compile
import shutil
import sys
from importlib import import_module
from importlib.util import cache_from_source
from pathlib import Path

import pytest
from helpers import with_env

PACKAGE = Path(__file__).parent / "package"
SOURCE = PACKAGE / "settings.py"


@pytest.fixture
def bytecode(monkeypatch):
    """Turns on bytecode writing, starting without any cached files."""
    cache = PACKAGE / "__pycache__"
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    shutil.rmtree(cache, ignore_errors=True)
    yield
    shutil.rmtree(cache, ignore_errors=True)


@with_env({"PORT": "99"})
def test_stale_bytecode_is_not_reused(bytecode):
    py_compile.compile(str(SOURCE))

    assert import_module(".package", __package__).PORT == 99


@with_env({"PORT": "99"})
def test_injected_bytecode_is_not_cached(bytecode):
    assert import_module(".package", __package__).PORT == 99
    assert not Path(cache_from_source(SOURCE)).exists()
