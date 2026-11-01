from pydantic_env_settings.import_machinery import env_import

with env_import():
    from example_settings import devel

from pprint import pp

pp({k: v for k, v in vars(devel).items() if not k.startswith("_")})
