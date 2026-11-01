from pydantic_module_settings import env_settings

from . import base

with env_settings(__name__, empty_as_unset=False):
    from . import devel
