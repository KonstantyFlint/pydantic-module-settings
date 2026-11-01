import os
from importlib import import_module
from typing import TYPE_CHECKING

from pydantic_module_settings import env_settings

if TYPE_CHECKING:
    from . import base as settings
else:
    with env_settings(__name__, prefix="APP_", empty_as_unset=True):
        settings = import_module(os.environ.get("SETTINGS_MODULE", f"{__name__}.base"))
