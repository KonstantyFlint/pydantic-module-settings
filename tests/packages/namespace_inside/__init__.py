from pydantic_env_settings import env_settings

with env_settings(__name__):
    from .sub.settings import *
