import os
from importlib import import_module

from pydantic_module_settings import env_settings

with env_settings(__name__, empty_as_unset=False):
    settings = import_module(
        os.environ.get("EXAMPLE_SETTINGS_MODULE", f"{__name__}.base")
    )
