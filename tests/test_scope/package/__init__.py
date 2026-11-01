import os
from importlib import import_module

from pydantic_env_settings import env_settings

with env_settings(f"{__name__}.settings", empty_as_unset=False):
    settings = import_module(
        os.environ.get("SCOPE_SETTINGS_MODULE", f"{__name__}.settings.base")
    )
