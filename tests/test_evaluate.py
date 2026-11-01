from pathlib import Path

import pytest

from pydantic_env_settings.evaluate import get_setting_value


@pytest.mark.parametrize(
    ("raw", "annotation", "expected"),
    [
        ("5", int, 5),
        ("true", bool, True),
        ('{"a": 1}', dict, {"a": 1}),
        ("[1, 2]", list[int], [1, 2]),
        ("null", int | None, None),
        ('"quoted"', str, "quoted"),
        ("hello", str, "hello"),
        ("123", str, "123"),
        ("", str, ""),
        ("/var/data", Path, Path("/var/data")),
    ],
)
def test_parses_env_value(monkeypatch, raw, annotation, expected):
    monkeypatch.setenv("SETTING", raw)

    assert get_setting_value("SETTING", annotation, empty_as_unset=False) == expected


def test_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("SETTING", raising=False)

    assert get_setting_value("SETTING", int, 3, empty_as_unset=True) == 3


def test_none_is_a_valid_default(monkeypatch):
    monkeypatch.delenv("SETTING", raising=False)

    assert get_setting_value("SETTING", int | None, None, empty_as_unset=False) is None


def test_invalid_value_names_the_variable_without_leaking_it(monkeypatch):
    monkeypatch.setenv("SETTING", "s3cret")

    with pytest.raises(RuntimeError, match="'SETTING' is invalid") as excinfo:
        get_setting_value("SETTING", int, empty_as_unset=False)

    assert "s3cret" not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__


@pytest.mark.parametrize("annotation", [int, str, int | None])
def test_empty_uses_default_when_enabled(monkeypatch, annotation):
    monkeypatch.setenv("SETTING", "")

    assert get_setting_value("SETTING", annotation, 5, empty_as_unset=True) == 5


def test_empty_counts_as_missing_when_enabled(monkeypatch):
    monkeypatch.setenv("SETTING", "")

    with pytest.raises(RuntimeError, match="'SETTING' must be set"):
        get_setting_value("SETTING", str, empty_as_unset=True)


def test_empty_overrides_default_when_disabled(monkeypatch):
    monkeypatch.setenv("SETTING", "")

    assert get_setting_value("SETTING", str, "x", empty_as_unset=False) == ""


def test_empty_is_validated_when_disabled(monkeypatch):
    monkeypatch.setenv("SETTING", "")

    with pytest.raises(RuntimeError, match="'SETTING' is invalid"):
        get_setting_value("SETTING", int, 5, empty_as_unset=False)


def test_whitespace_is_not_empty(monkeypatch):
    monkeypatch.setenv("SETTING", " ")

    assert get_setting_value("SETTING", str, "x", empty_as_unset=True) == " "
