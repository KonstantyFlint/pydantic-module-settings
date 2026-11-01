from pydantic_module_settings import env_settings

with env_settings(__name__, empty_as_unset=True):
    from .settings import *
