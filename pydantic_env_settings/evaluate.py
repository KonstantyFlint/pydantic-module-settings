import os
from typing import cast

from pydantic import TypeAdapter, ValidationError


class UnsetType:
    pass


UNSET = UnsetType()
UnsetType.__new__ = None  # type: ignore


def parse_setting[T](name: str, annotation: type[T], raw: str) -> T:
    """Parse `raw` as JSON, falling back to the plain string (`NAME=hello`)."""
    adapter = TypeAdapter(annotation)
    try:
        return adapter.validate_json(raw)
    except ValidationError:
        pass
    try:
        return adapter.validate_python(raw)
    except ValidationError as exc:
        # `from None`, and only the messages: pydantic's own error text quotes
        # the input, and settings values may be secrets.
        reasons = "; ".join(error["msg"] for error in exc.errors())
        raise RuntimeError(
            f"Environment variable '{name}' is invalid: {reasons}"
        ) from None


def get_setting_value[T](
    name: str,
    annotation: type[T],
    default: T | UnsetType = UNSET,
) -> T:
    if name in os.environ:
        return parse_setting(name, annotation, os.environ[name])
    if default is UNSET:
        raise RuntimeError(f"Environment variable '{name}' must be set.")
    return cast(T, default)
