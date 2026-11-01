import importlib
import sys

import pytest

from pydantic_env_settings.import_machinery import env_import

EXAMPLE_SETTINGS = {
    "example_settings/__init__.py": "",
    "example_settings/base.py": "X: int\n",
    "example_settings/devel.py": (
        "from example_settings.base import *\n\nY: int = X * 5\nZ: dict\n"
    ),
}


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Writes modules to an importable directory, forgetting them afterwards."""
    monkeypatch.syspath_prepend(tmp_path)
    roots = set()

    def write(files):
        for name, source in files.items():
            path = tmp_path / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(source)
            roots.add(name.split("/")[0].removesuffix(".py"))
        importlib.invalidate_caches()

    yield write

    for name in list(sys.modules):
        if name.split(".")[0] in roots:
            del sys.modules[name]


def load(name):
    with env_import():
        return importlib.import_module(name)


def test_settings_can_build_on_imported_settings(project, monkeypatch):
    project(EXAMPLE_SETTINGS)
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Z", '{"a": 1}')
    monkeypatch.delenv("Y", raising=False)

    devel = load("example_settings.devel")

    assert (devel.X, devel.Y, devel.Z) == (2, 10, {"a": 1})


def test_env_overrides_default(project, monkeypatch):
    project(EXAMPLE_SETTINGS)
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Y", "99")
    monkeypatch.setenv("Z", "{}")

    assert load("example_settings.devel").Y == 99


def test_missing_required_setting_raises(project, monkeypatch):
    project({"settings.py": "REQUIRED_SETTING: int\n"})
    monkeypatch.delenv("REQUIRED_SETTING", raising=False)

    with pytest.raises(RuntimeError, match="'REQUIRED_SETTING' must be set"):
        load("settings")


def test_conditional_module_level_settings_are_injected(project, monkeypatch):
    project({"settings.py": "if True:\n    NESTED: int = 1\n"})
    monkeypatch.setenv("NESTED", "99")

    assert load("settings").NESTED == 99
