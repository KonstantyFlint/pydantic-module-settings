import sys
from importlib import import_module

import pytest


@pytest.mark.parametrize("value", [None, "nope"])
def test_finder_is_removed_when_import_fails(monkeypatch, value):
    monkeypatch.delenv("FOO_REQUIRED", raising=False)
    if value:
        monkeypatch.setenv("FOO_REQUIRED", value)
    meta_path = list(sys.meta_path)

    with pytest.raises(RuntimeError):
        import_module(".package", __package__)

    assert sys.meta_path == meta_path


def test_missing_setting_error_names_prefixed_variable(monkeypatch):
    monkeypatch.delenv("FOO_REQUIRED", raising=False)
    monkeypatch.setenv("REQUIRED", "1")

    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' must be set"):
        import_module(".package", __package__)


def test_invalid_setting_error_names_prefixed_variable(monkeypatch):
    monkeypatch.setenv("FOO_REQUIRED", "nope")

    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' is invalid"):
        import_module(".package", __package__)
