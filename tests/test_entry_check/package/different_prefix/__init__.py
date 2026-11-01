from pydantic_module_settings import env_settings

with env_settings(__name__, prefix="FOO_", empty_as_unset=False):
    from . import base

with env_settings(__name__, prefix="BAR_", empty_as_unset=False):
    from . import base
