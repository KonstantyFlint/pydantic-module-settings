from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BeforeValidator, Field


def split_csv(value: object) -> object:
    return value.split(",") if isinstance(value, str) else value


def require_even(value: int) -> int:
    if value % 2:
        raise ValueError("must be even")
    return value


CREATED_AT: datetime
RELEASED_ON: date
LEVEL: Literal[1, 2, 3] = 1
IDS: Annotated[list[int], BeforeValidator(split_csv), AfterValidator(sorted)]
PORT: Annotated[int, Field(ge=1024), AfterValidator(require_even)] = 8000
