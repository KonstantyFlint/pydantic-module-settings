from importlib import import_module


def test_empty_prefixed_variable_counts_as_unset_when_enabled(monkeypatch):
    monkeypatch.setenv("FOO_VALUE", "")

    assert import_module(".package.unset", __package__).VALUE == 5


def test_empty_variable_stays_empty_when_disabled(monkeypatch):
    monkeypatch.setenv("TEXT", "")

    assert import_module(".package.kept", __package__).TEXT == ""
