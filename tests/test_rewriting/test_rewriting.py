from importlib import import_module


def test_function_and_class_bodies_are_not_rewritten(monkeypatch):
    monkeypatch.setenv("PORT", "99")

    settings = import_module(".package", __package__)

    assert settings.CLASS_PORT == 1
    assert settings.ASYNC_PORT == 2
    assert settings.LOCAL_PORT == 3


def test_conditional_module_level_settings_are_rewritten(monkeypatch):
    monkeypatch.setenv("NESTED", "99")

    assert import_module(".package", __package__).NESTED == 99
