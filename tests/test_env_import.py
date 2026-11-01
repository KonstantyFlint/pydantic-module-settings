import importlib
import sys
from pathlib import Path

import pytest

from pydantic_env_settings.import_machinery import env_import

PACKAGES = Path(__file__).parent / "packages"


@pytest.fixture(autouse=True)
def forget_packages():
    """Lets every test import the sample packages from scratch."""
    yield
    for name, module in list(sys.modules.items()):
        if PACKAGES in Path(getattr(module, "__file__", None) or "").parents:
            del sys.modules[name]


def load(name, *scope):
    with env_import(*(scope or [name])):
        return importlib.import_module(name)


def test_settings_can_build_on_imported_settings(monkeypatch):
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Z", '{"a": 1}')
    monkeypatch.delenv("Y", raising=False)

    devel = load("example_settings.devel", "example_settings")

    assert (devel.X, devel.Y, devel.Z) == (2, 10, {"a": 1})


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Y", "99")
    monkeypatch.setenv("Z", "{}")

    assert load("example_settings.devel", "example_settings").Y == 99


def test_missing_required_setting_raises(monkeypatch):
    monkeypatch.delenv("REQUIRED_SETTING", raising=False)

    with pytest.raises(RuntimeError, match="'REQUIRED_SETTING' must be set"):
        load("required_settings")


def test_modules_outside_scope_are_not_injected(monkeypatch):
    monkeypatch.setenv("LIMIT", "99")

    settings = load("importing_settings")

    assert settings.helper_module.LIMIT == 1
    assert settings.HELPER_LIMIT == 1
    assert not hasattr(settings.helper_module, "__get_setting_value__")


def test_sibling_of_scoped_package_is_not_injected(monkeypatch):
    monkeypatch.setenv("LIMIT", "99")
    monkeypatch.setenv("B", "3")

    base = load("sample_app.settings.base", "sample_app.settings")

    assert (base.A, base.B) == (1, 3)


def test_scope_does_not_match_name_prefix(monkeypatch):
    monkeypatch.setenv("VALUE", "99")

    assert load("settings_extra", "settings").VALUE == 1


def test_several_scopes(monkeypatch):
    monkeypatch.setenv("A", "1")
    monkeypatch.setenv("B", "2")

    settings = load("chained_second", "chained_first", "chained_second")

    assert (settings.A, settings.B) == (1, 2)


def test_conditional_module_level_settings_are_injected(monkeypatch):
    monkeypatch.setenv("NESTED", "99")

    assert load("conditional_settings").NESTED == 99
