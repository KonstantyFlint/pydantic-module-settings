import sys
from typing import TYPE_CHECKING, assert_type

import pytest
from helpers import with_env

DEVEL = f"{__package__}.package.devel"

if TYPE_CHECKING:
    # Checked by pyright: the selected module is typed as `base`, whichever it is.
    from .package import settings as static_settings

    assert_type(static_settings.PORT, int)
    assert_type(static_settings.DEBUG, bool)
    _ = static_settings.URL  # pyright: ignore[reportAttributeAccessIssue]


@with_env({})
def test_base_is_selected_by_default():
    from .package import settings

    assert settings.__name__ == f"{__package__}.package.base"
    assert (settings.DEBUG, settings.PORT) == (False, 8000)


@with_env({"APP_PORT": "9000", "APP_DEBUG": "true"})
def test_settings_are_read_with_the_prefix():
    from .package import settings

    assert (settings.DEBUG, settings.PORT) == (True, 9000)


@with_env({"SETTINGS_MODULE": DEVEL, "APP_PORT": "9000"})
def test_selected_module_builds_on_base_and_overrides_it():
    from .package import settings

    assert settings.__name__ == DEVEL
    assert settings.DEBUG is True
    assert settings.PORT == 9000
    assert settings.URL == "http://localhost:9000"  # pyright: ignore[reportAttributeAccessIssue]


@with_env({"SETTINGS_MODULE": DEVEL, "APP_TIMEOUT": "60"})
def test_selected_module_has_settings_defined_only_in_base():
    from .package import settings

    assert settings.TIMEOUT == 60


@with_env({"SETTINGS_MODULE": DEVEL, "APP_DEBUG": "false"})
def test_selected_module_defaults_can_be_overridden_by_env():
    from .package import settings

    assert settings.DEBUG is False


@with_env({"APP_PORT": ""})
def test_empty_variable_uses_the_default():
    from .package import settings

    assert settings.PORT == 8000


@with_env({"PORT": "9000"})
def test_unprefixed_variable_is_ignored():
    from .package import settings

    assert settings.PORT == 8000


@with_env({"APP_PORT": "nope"})
def test_invalid_value_raises_and_removes_the_finder():
    meta_path = list(sys.meta_path)

    with pytest.raises(RuntimeError, match="'APP_PORT' is invalid"):
        from .package import settings  # noqa: F401

    assert sys.meta_path == meta_path


@with_env({"SETTINGS_MODULE": f"{__package__}.package.nope"})
def test_unknown_module_raises():
    with pytest.raises(ModuleNotFoundError, match=r"package\.nope"):
        from .package import settings  # noqa: F401
