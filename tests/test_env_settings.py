import importlib
import shutil
import sys
from importlib.machinery import PathFinder
from pathlib import Path

import pytest

from pydantic_env_settings.import_machinery import (
    EnvSettingsFinder,
    env_import,
)

PACKAGES = Path(__file__).parent / "packages"


@pytest.fixture(autouse=True)
def forget_packages():
    """Lets every test import the sample packages from scratch."""
    yield
    for name, module in list(sys.modules.items()):
        if PACKAGES in Path(getattr(module, "__file__", None) or "").parents:
            del sys.modules[name]


@pytest.fixture
def bytecode(monkeypatch):
    """Turns on bytecode writing, starting without any cached files."""
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    shutil.rmtree(PACKAGES / "bytecode_settings" / "__pycache__", ignore_errors=True)
    yield
    shutil.rmtree(PACKAGES / "bytecode_settings" / "__pycache__", ignore_errors=True)


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
        load("required_settings.settings")


def test_modules_outside_scope_are_not_injected(monkeypatch):
    monkeypatch.setenv("LIMIT", "99")

    settings = load("outside_scope.settings")

    assert settings.helper.LIMIT == 1
    assert settings.HELPER_LIMIT == 1
    assert not hasattr(settings.helper, "__get_setting_value__")


def test_sibling_of_scoped_package_is_not_injected(monkeypatch):
    monkeypatch.setenv("LIMIT", "99")
    monkeypatch.setenv("B", "3")

    base = load("sample_app.settings.base", "sample_app.settings")

    assert (base.A, base.B) == (1, 3)


def test_scope_does_not_match_name_prefix(monkeypatch):
    monkeypatch.setenv("VALUE", "99")

    assert load("prefix_scope.settings_extra", "prefix_scope.settings").VALUE == 1


def test_several_scopes(monkeypatch):
    monkeypatch.setenv("A", "1")
    monkeypatch.setenv("B", "2")

    settings = load("multi_scope.second", "multi_scope.first", "multi_scope.second")

    assert (settings.A, settings.B) == (1, 2)


def test_function_and_class_bodies_are_not_injected(monkeypatch):
    monkeypatch.setenv("PORT", "99")

    settings = load("nested_scopes.settings")

    assert settings.CLASS_PORT == 1
    assert settings.ASYNC_PORT == 2
    assert settings.LOCAL_PORT == 3


def test_conditional_module_level_settings_are_injected(monkeypatch):
    monkeypatch.setenv("NESTED", "99")

    assert load("conditional_settings.settings").NESTED == 99


@pytest.mark.parametrize("failing", ["missing", "invalid"])
def test_finder_is_removed_when_import_fails(monkeypatch, failing):
    monkeypatch.delenv("REQUIRED_SETTING", raising=False)
    if failing == "invalid":
        monkeypatch.setenv("REQUIRED_SETTING", "nope")
    meta_path = list(sys.meta_path)

    with pytest.raises(RuntimeError):
        load("required_settings.settings")

    assert sys.meta_path == meta_path


def test_bytecode_from_plain_import_is_not_reused(monkeypatch, bytecode):
    monkeypatch.setenv("PORT", "99")

    assert importlib.import_module("bytecode_settings.settings").PORT == 1
    del sys.modules["bytecode_settings.settings"]

    assert load("bytecode_settings.settings").PORT == 99


def test_injected_bytecode_is_not_cached(monkeypatch, bytecode):
    monkeypatch.setenv("PORT", "99")

    assert load("bytecode_settings.settings").PORT == 99
    del sys.modules["bytecode_settings.settings"]

    assert importlib.import_module("bytecode_settings.settings").PORT == 1


def test_finder_target_defaults_to_none(monkeypatch):
    calls = []
    monkeypatch.setattr(
        PathFinder, "find_spec", lambda *args: calls.append(args)
    )

    EnvSettingsFinder(["settings"]).find_spec("settings", None)

    assert calls == [("settings", None, None)]
