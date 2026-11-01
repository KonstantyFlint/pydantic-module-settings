import os
from importlib import import_module

from pydantic_env_settings import env_settings

with env_settings(__name__):
    settings = import_module(
        os.environ.get("EXAMPLE_SETTINGS_MODULE", f"{__name__}.base")
    )
