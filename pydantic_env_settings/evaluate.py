import os
from typing import cast

from pydantic import TypeAdapter


class UnsetType:
    pass


UNSET = UnsetType()
UnsetType.__new__ = None  # type: ignore


def get_setting_value[T](
    name: str,
    annotation: type[T],
    default: T | UnsetType = UNSET,
) -> T:
    if name in os.environ:
        return TypeAdapter(annotation).validate_json(os.environ[name])
    if default is UNSET:
        raise RuntimeError(f"Environment variable '{name}' must be set.")
    return cast(T, default)
