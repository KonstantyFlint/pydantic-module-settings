import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

import pytest
from helpers import with_env
from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    StringConstraints,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)

from pydantic_module_settings.evaluate import get_setting_value


def split_csv(value: object) -> object:
    return value.split(",") if isinstance(value, str) else value


def parse_duration(value: object) -> object:
    if isinstance(value, str) and (match := re.fullmatch(r"(\d+)([sm])", value)):
        amount, unit = match.groups()
        return timedelta(seconds=int(amount) * {"s": 1, "m": 60}[unit])
    return value


def require_even(value: int) -> int:
    if value % 2:
        raise ValueError("must be even")
    return value


def fall_back_to_zero(value: object, handler: ValidatorFunctionWrapHandler) -> object:
    try:
        return handler(value)
    except ValidationError:
        return 0


Csv = Annotated[list[int], BeforeValidator(split_csv), AfterValidator(sorted)]
Duration = Annotated[timedelta, BeforeValidator(parse_duration)]
EvenPort = Annotated[int, Field(ge=1024, le=65535), AfterValidator(require_even)]
Normalized = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)]
OrZero = Annotated[int, WrapValidator(fall_back_to_zero)]


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
        ("2026-01-02T03:04:05", datetime, datetime(2026, 1, 2, 3, 4, 5)),
        (
            "2026-01-02T03:04:05Z",
            datetime,
            datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
        ),
        ('"2026-01-02T03:04:05"', datetime, datetime(2026, 1, 2, 3, 4, 5)),
        ("2026-01-02", datetime, datetime(2026, 1, 2)),
        ("0", datetime, datetime(1970, 1, 1, tzinfo=UTC)),
        ("2026-01-02", date, date(2026, 1, 2)),
        ('"2026-01-02"', date, date(2026, 1, 2)),
        ("2", Literal[1, 2, 3], 2),
        ("b", Literal["a", "b"], "b"),
        ("1", Literal["1", "2"], "1"),
        ("1", Literal[1, "a"], 1),
        ("a", Literal[1, "a"], "a"),
        ("3,1,2", Csv, [1, 2, 3]),
        ("[3, 1, 2]", Csv, [1, 2, 3]),
        ("5", Csv, [5]),
        ("5m", Duration, timedelta(minutes=5)),
        ("PT30S", Duration, timedelta(seconds=30)),
        ("8080", EvenPort, 8080),
        ("  MiXeD  ", Normalized, "mixed"),
        ("5", OrZero, 5),
        ("nope", OrZero, 0),
    ],
)
def test_parses_env_value(raw, annotation, expected):
    with with_env({"SETTING": raw}):
        assert (
            get_setting_value("SETTING", annotation, empty_as_unset=False) == expected
        )


@with_env({})
@pytest.mark.parametrize(
    ("raw", "annotation", "reason"),
    [
        ("nope", datetime, "valid datetime"),
        ("2026-13-01", date, "valid date"),
        ("2026-01-02T03:04:05", date, "zero time"),
        ("4", Literal[1, 2, 3], "Input should be 1, 2 or 3"),
        ("one", Literal[1, 2, 3], "Input should be 1, 2 or 3"),
        ("x,y", Csv, "valid integer"),
        ("5h", Duration, "valid timedelta"),
        ("8081", EvenPort, "must be even"),
        ("80", EvenPort, "greater than or equal to 1024"),
        ("70000", EvenPort, "less than or equal to 65535"),
    ],
)
def test_invalid_value_gives_the_reason(raw, annotation, reason):
    with (
        with_env({"SETTING": raw}),
        pytest.raises(RuntimeError, match=rf"'SETTING' is invalid: .*{reason}"),
    ):
        get_setting_value("SETTING", annotation, empty_as_unset=False)


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
