from importlib import import_module


def test_prefix_is_used_by_settings_importing_each_other(monkeypatch):
    monkeypatch.setenv("FOO_ABC", "2")
    monkeypatch.delenv("FOO_DEF", raising=False)

    settings = import_module(".package", __package__)

    assert (settings.ABC, settings.DEF) == (2, 10)


def test_prefixed_setting_ignores_unprefixed_variable(monkeypatch):
    monkeypatch.delenv("FOO_ABC", raising=False)
    monkeypatch.setenv("ABC", "2")

    assert import_module(".package", __package__).ABC == 1


def test_prefix_is_case_sensitive(monkeypatch):
    monkeypatch.delenv("FOO_ABC", raising=False)
    monkeypatch.setenv("foo_ABC", "2")

    assert import_module(".package", __package__).ABC == 1
