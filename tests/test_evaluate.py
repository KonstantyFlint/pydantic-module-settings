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

    assert get_setting_value("SETTING", annotation) == expected


def test_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("SETTING", raising=False)

    assert get_setting_value("SETTING", int, 3) == 3


def test_none_is_a_valid_default(monkeypatch):
    monkeypatch.delenv("SETTING", raising=False)

    assert get_setting_value("SETTING", int | None, None) is None


def test_invalid_value_names_the_variable_without_leaking_it(monkeypatch):
    monkeypatch.setenv("SETTING", "s3cret")

    with pytest.raises(RuntimeError, match="'SETTING' is invalid") as excinfo:
        get_setting_value("SETTING", int)

    assert "s3cret" not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__
