import os
from importlib import import_module

from pydantic_env_settings import env_settings

with env_settings(f"{__name__}.settings"):
    settings = import_module(
        os.environ.get("SELECTOR_SETTINGS_MODULE", f"{__name__}.settings.base")
    )
