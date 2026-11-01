from pydantic_env_settings import env_settings

with env_settings(__name__, prefix="FOO_", empty_as_unset=True):
    from .settings import *
