from datetime import date, datetime
from importlib import import_module

import pytest
from helpers import with_env

ENV = {
    "CREATED_AT": "2026-01-02T03:04:05",
    "RELEASED_ON": "2026-01-02",
    "LEVEL": "3",
    "IDS": "3,1,2",
    "PORT": "8080",
}


@with_env(ENV)
def test_annotations_are_evaluated_in_the_settings_module():
    settings = import_module(".package", __package__)

    assert settings.CREATED_AT == datetime(2026, 1, 2, 3, 4, 5)
    assert settings.RELEASED_ON == date(2026, 1, 2)
    assert settings.LEVEL == 3
    assert settings.IDS == [1, 2, 3]
    assert settings.PORT == 8080


@pytest.mark.parametrize(
    ("name", "value", "reason"),
    [
        ("LEVEL", "4", "Input should be 1, 2 or 3"),
        ("PORT", "8081", "must be even"),
        ("PORT", "80", "greater than or equal to 1024"),
    ],
)
def test_validators_defined_in_the_settings_module_reject_values(name, value, reason):
    with (
        with_env({**ENV, name: value}),
        pytest.raises(RuntimeError, match=rf"'{name}' is invalid: .*{reason}"),
    ):
        import_module(".package", __package__)
