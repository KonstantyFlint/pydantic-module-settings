from preloaded_settings import base
from pydantic_env_settings import env_settings

with env_settings(__name__, empty_as_unset=False):
    from . import devel
