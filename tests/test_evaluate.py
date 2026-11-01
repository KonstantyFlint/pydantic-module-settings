from pathlib import Path

import pytest
from helpers import with_env

from pydantic_module_settings.evaluate import get_setting_value


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
def test_parses_env_value(raw, annotation, expected):
    with with_env({"SETTING": raw}):
        assert (
            get_setting_value("SETTING", annotation, empty_as_unset=False) == expected
        )


@with_env({})
def test_returns_default_when_unset():
    assert get_setting_value("SETTING", int, 3, empty_as_unset=True) == 3


@with_env({})
def test_none_is_a_valid_default():
    assert get_setting_value("SETTING", int | None, None, empty_as_unset=False) is None


@with_env({"SETTING": "s3cret"})
def test_invalid_value_names_the_variable_without_leaking_it():
    with pytest.raises(RuntimeError, match="'SETTING' is invalid") as excinfo:
        get_setting_value("SETTING", int, empty_as_unset=False)

    assert "s3cret" not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__


@pytest.mark.parametrize("annotation", [int, str, int | None])
@with_env({"SETTING": ""})
def test_empty_uses_default_when_enabled(annotation):
    assert get_setting_value("SETTING", annotation, 5, empty_as_unset=True) == 5


@with_env({"SETTING": ""})
def test_empty_counts_as_missing_when_enabled():
    with pytest.raises(RuntimeError, match="'SETTING' must be set"):
        get_setting_value("SETTING", str, empty_as_unset=True)


@with_env({"SETTING": ""})
def test_empty_overrides_default_when_disabled():
    assert get_setting_value("SETTING", str, "x", empty_as_unset=False) == ""


@with_env({"SETTING": ""})
def test_empty_is_validated_when_disabled():
    with pytest.raises(RuntimeError, match="'SETTING' is invalid"):
        get_setting_value("SETTING", int, 5, empty_as_unset=False)


@with_env({"SETTING": " "})
def test_whitespace_is_not_empty():
    assert get_setting_value("SETTING", str, "x", empty_as_unset=True) == " "
