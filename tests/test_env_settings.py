import importlib
import py_compile
import shutil
import sys
from importlib.machinery import PathFinder
from importlib.util import cache_from_source
from pathlib import Path

import pytest

from pydantic_env_settings.import_machinery import EnvSettingsFinder

PACKAGES = Path(__file__).parent / "packages"
BYTECODE_SOURCE = PACKAGES / "bytecode_settings" / "settings.py"


@pytest.fixture(autouse=True)
def forget_packages():
    """Lets every test import the sample packages from scratch."""
    meta_path = list(sys.meta_path)
    yield
    sys.meta_path[:] = meta_path
    roots = {path.name for path in PACKAGES.iterdir()}
    for name in list(sys.modules):
        if name.split(".")[0] in roots:
            del sys.modules[name]


@pytest.fixture
def bytecode(monkeypatch):
    """Turns on bytecode writing, starting without any cached files."""
    cache = PACKAGES / "bytecode_settings" / "__pycache__"
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    shutil.rmtree(cache, ignore_errors=True)
    yield
    shutil.rmtree(cache, ignore_errors=True)


load = importlib.import_module


def test_default_settings_are_selected(monkeypatch):
    monkeypatch.setenv("X", "2")
    monkeypatch.delenv("EXAMPLE_SETTINGS_MODULE", raising=False)

    settings = load("example_settings").settings

    assert settings.__name__ == "example_settings.base"
    assert settings.X == 2


def test_selected_settings_can_build_on_other_settings(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SETTINGS_MODULE", "example_settings.devel")
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Z", '{"a": 1}')
    monkeypatch.delenv("Y", raising=False)

    settings = load("example_settings").settings

    assert (settings.X, settings.Y, settings.Z) == (2, 10, {"a": 1})


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SETTINGS_MODULE", "example_settings.devel")
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Y", "99")
    monkeypatch.setenv("Z", "{}")

    assert load("example_settings").settings.Y == 99


def test_parent_package_can_select_settings(monkeypatch):
    monkeypatch.setenv("PORT", "99")
    monkeypatch.setenv("LIMIT", "99")
    monkeypatch.delenv("SELECTOR_SETTINGS_MODULE", raising=False)

    app = load("selector_app")

    assert app.settings.__name__ == "selector_app.settings.base"
    assert app.settings.PORT == 99
    assert load("selector_app.utils").LIMIT == 1


def test_finder_is_removed_after_the_block():
    meta_path = list(sys.meta_path)

    load("sample_app.settings")

    assert sys.meta_path == meta_path


@pytest.mark.parametrize("value", [None, "nope"])
def test_finder_is_removed_when_import_fails(monkeypatch, value):
    monkeypatch.delenv("REQUIRED_SETTING", raising=False)
    if value:
        monkeypatch.setenv("REQUIRED_SETTING", value)
    meta_path = list(sys.meta_path)

    with pytest.raises(RuntimeError):
        load("required_settings")

    assert sys.meta_path == meta_path


def test_missing_required_setting_raises(monkeypatch):
    monkeypatch.delenv("REQUIRED_SETTING", raising=False)

    with pytest.raises(RuntimeError, match="'REQUIRED_SETTING' must be set"):
        load("required_settings")


def test_modules_outside_package_are_not_injected(monkeypatch):
    monkeypatch.setenv("LIMIT", "99")
    monkeypatch.setenv("B", "3")

    settings = load("sample_app.settings")

    assert (settings.A, settings.B) == (1, 3)
    assert settings.utils.LIMIT == 1
    assert not hasattr(settings.utils, "__get_setting_value__")


def test_scope_does_not_match_name_prefix(monkeypatch):
    monkeypatch.setenv("VALUE", "99")

    assert load("prefix_scope.settings").EXTRA == 1


def test_prefix_is_used_by_settings_importing_each_other(monkeypatch):
    monkeypatch.setenv("FOO_ABC", "2")
    monkeypatch.delenv("FOO_DEF", raising=False)

    settings = load("prefixed_settings")

    assert (settings.ABC, settings.DEF) == (2, 10)


def test_prefixed_setting_ignores_unprefixed_variable(monkeypatch):
    monkeypatch.delenv("FOO_ABC", raising=False)
    monkeypatch.setenv("ABC", "2")

    assert load("prefixed_settings").ABC == 1


def test_prefix_is_case_sensitive(monkeypatch):
    monkeypatch.delenv("FOO_ABC", raising=False)
    monkeypatch.setenv("foo_ABC", "2")

    assert load("prefixed_settings").ABC == 1


def test_missing_setting_error_names_prefixed_variable(monkeypatch):
    monkeypatch.delenv("FOO_REQUIRED", raising=False)
    monkeypatch.setenv("REQUIRED", "1")

    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' must be set"):
        load("prefixed_required")


def test_invalid_setting_error_names_prefixed_variable(monkeypatch):
    monkeypatch.setenv("FOO_REQUIRED", "nope")

    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' is invalid"):
        load("prefixed_required")


def test_function_and_class_bodies_are_not_injected(monkeypatch):
    monkeypatch.setenv("PORT", "99")

    settings = load("nested_scopes")

    assert settings.CLASS_PORT == 1
    assert settings.ASYNC_PORT == 2
    assert settings.LOCAL_PORT == 3


def test_conditional_module_level_settings_are_injected(monkeypatch):
    monkeypatch.setenv("NESTED", "99")

    assert load("conditional_settings").NESTED == 99


def test_invalid_value_raises(monkeypatch):
    monkeypatch.setenv("REQUIRED_SETTING", "nope")

    with pytest.raises(RuntimeError, match="'REQUIRED_SETTING' is invalid"):
        load("required_settings")


def test_dependency_imported_before_hook_raises():
    with pytest.raises(
        RuntimeError, match=r"already imported differently: preloaded_settings\.base\.$"
    ):
        load("preloaded_settings")

    assert "preloaded_settings.devel" not in sys.modules


def test_different_prefix_for_imported_settings_raises():
    with pytest.raises(
        RuntimeError, match=r"already imported differently: mixed_prefix\.base\.$"
    ):
        load("mixed_prefix")


def test_no_prefix_for_settings_imported_with_prefix_raises():
    with pytest.raises(RuntimeError, match=r"differently: dropped_prefix\.base\.$"):
        load("dropped_prefix")


def test_same_prefix_can_be_used_again(monkeypatch):
    monkeypatch.setenv("FOO_VALUE", "2")

    assert load("repeated_prefix").base.VALUE == 2


def test_reloading_allows_namespace_subpackage():
    settings = load("namespace_inside")

    assert importlib.reload(settings).VALUE == 1


def test_stale_bytecode_is_not_reused(monkeypatch, bytecode):
    py_compile.compile(BYTECODE_SOURCE)
    monkeypatch.setenv("PORT", "99")

    assert load("bytecode_settings").PORT == 99


def test_injected_bytecode_is_not_cached(monkeypatch, bytecode):
    monkeypatch.setenv("PORT", "99")

    assert load("bytecode_settings").PORT == 99
    assert not Path(cache_from_source(BYTECODE_SOURCE)).exists()


def test_finder_target_defaults_to_none(monkeypatch):
    calls = []
    monkeypatch.setattr(PathFinder, "find_spec", lambda *args: calls.append(args))

    EnvSettingsFinder("settings").find_spec("settings.base", None)

    assert calls == [("settings.base", None, None)]
