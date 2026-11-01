from importlib import import_module

from helpers import with_env


@with_env({"PORT": "99"})
def test_function_and_class_bodies_are_not_rewritten():
    settings = import_module(".package", __package__)

    assert settings.CLASS_PORT == 1
    assert settings.ASYNC_PORT == 2
    assert settings.LOCAL_PORT == 3


@with_env({"NESTED": "99"})
def test_conditional_module_level_settings_are_rewritten():
    assert import_module(".package", __package__).NESTED == 99
