from importlib import import_module

from helpers import with_env


@with_env({"FOO_ABC": "2"})
def test_prefix_is_used_by_settings_importing_each_other():
    settings = import_module(".package", __package__)

    assert (settings.ABC, settings.DEF) == (2, 10)


@with_env({"ABC": "2"})
def test_prefixed_setting_ignores_unprefixed_variable():
    assert import_module(".package", __package__).ABC == 1


@with_env({"foo_ABC": "2"})
def test_prefix_is_case_sensitive():
    assert import_module(".package", __package__).ABC == 1
