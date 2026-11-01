from importlib import import_module


def test_default_settings_are_selected(monkeypatch):
    monkeypatch.setenv("X", "2")
    monkeypatch.delenv("EXAMPLE_SETTINGS_MODULE", raising=False)

    settings = import_module(".package", __package__).settings

    assert settings.__name__ == f"{__package__}.package.base"
    assert settings.X == 2


def test_selected_settings_can_build_on_other_settings(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SETTINGS_MODULE", f"{__package__}.package.devel")
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Z", '{"a": 1}')
    monkeypatch.delenv("Y", raising=False)

    settings = import_module(".package", __package__).settings

    assert (settings.X, settings.Y, settings.Z) == (2, 10, {"a": 1})


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SETTINGS_MODULE", f"{__package__}.package.devel")
    monkeypatch.setenv("X", "2")
    monkeypatch.setenv("Y", "99")
    monkeypatch.setenv("Z", "{}")

    assert import_module(".package", __package__).settings.Y == 99
