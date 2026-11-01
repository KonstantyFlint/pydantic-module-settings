import sys
from importlib import import_module

from helpers import with_env


@with_env({"B": "3"})
def test_parent_package_can_select_settings():
    settings = import_module(".package", __package__).settings

    assert settings.__name__ == f"{__package__}.package.settings.base"
    assert settings.B == 3


@with_env({"LIMIT": "99"})
def test_modules_outside_scope_are_not_injected():
    settings = import_module(".package", __package__).settings

    assert settings.A == 1
    assert settings.utils.LIMIT == 1
    assert not hasattr(settings.utils, "__get_setting_value__")


@with_env({"VALUE": "99"})
def test_scope_does_not_match_name_prefix():
    assert import_module(".package", __package__).settings.EXTRA == 1


@with_env({})
def test_finder_is_removed_after_the_block():
    meta_path = list(sys.meta_path)

    import_module(".package", __package__)

    assert sys.meta_path == meta_path
