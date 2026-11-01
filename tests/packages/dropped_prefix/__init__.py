from pydantic_env_settings import env_settings

with env_settings(__name__, prefix="FOO_"):
    from . import base

with env_settings(__name__):
    from . import base
