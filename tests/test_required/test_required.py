import sys
from importlib import import_module

import pytest
from helpers import with_env


@pytest.mark.parametrize("env", [{}, {"FOO_REQUIRED": "nope"}])
def test_finder_is_removed_when_import_fails(env):
    meta_path = list(sys.meta_path)

    with with_env(env), pytest.raises(RuntimeError):
        import_module(".package", __package__)

    assert sys.meta_path == meta_path


@with_env({"REQUIRED": "1"})
def test_missing_setting_error_names_prefixed_variable():
    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' must be set"):
        import_module(".package", __package__)


@with_env({"FOO_REQUIRED": "nope"})
def test_invalid_setting_error_names_prefixed_variable():
    with pytest.raises(RuntimeError, match="'FOO_REQUIRED' is invalid"):
        import_module(".package", __package__)
