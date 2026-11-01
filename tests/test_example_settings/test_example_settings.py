from importlib import import_module

from helpers import with_env


@with_env({"X": "2"})
def test_default_settings_are_selected():
    settings = import_module(".package", __package__).settings

    assert settings.__name__ == f"{__package__}.package.base"
    assert settings.X == 2


@with_env(
    {
        "EXAMPLE_SETTINGS_MODULE": f"{__package__}.package.devel",
        "X": "2",
        "Z": '{"a": 1}',
    }
)
def test_selected_settings_can_build_on_other_settings():
    settings = import_module(".package", __package__).settings

    assert (settings.X, settings.Y, settings.Z) == (2, 10, {"a": 1})


@with_env(
    {
        "EXAMPLE_SETTINGS_MODULE": f"{__package__}.package.devel",
        "X": "2",
        "Y": "99",
        "Z": "{}",
    }
)
def test_env_overrides_default():
    assert import_module(".package", __package__).settings.Y == 99
