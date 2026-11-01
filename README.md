# pydantic-module-settings

Write settings as plain, annotated Python modules, and have them read from
environment variables and validated by [pydantic](https://docs.pydantic.dev).

```python
PORT: int = 8000      # read from PORT, 8000 if it's not set
DATABASE_URL: str     # read from DATABASE_URL, required
```

There are no classes to define and no instances to pass around. Settings stay
ordinary modules, so they can compute values from each other and build on one
another, like any other Python code.

Requires Python 3.13 or newer.

## Installation

```shell
pip install pydantic-module-settings
```

## Quick start

Create a settings package:

```python
# settings/base.py
DEBUG: bool = False
PORT: int = 8000
DATABASE_URL: str
ALLOWED_HOSTS: list[str] = []
```

```python
# settings/__init__.py
from pydantic_module_settings import env_settings

with env_settings(__name__, prefix="APP_", empty_as_unset=True):
    from .base import *
```

Then import it anywhere:

```python
import settings

print(settings.PORT, settings.DATABASE_URL, settings.ALLOWED_HOSTS)
```

```shell
$ APP_PORT=9000 APP_DATABASE_URL=postgres://db APP_ALLOWED_HOSTS='["a.com"]' python main.py
9000 postgres://db ['a.com']
```

## How it works

While the `with` block is active, modules inside the given package are rewritten
as they're imported. Every annotated name at module level becomes a lookup of an
environment variable, validated against its annotation:

- If the variable is set, its value is used.
- If it isn't, the default is used, or a `RuntimeError` is raised if there is none.

Everything else is left alone: unannotated names, class and function bodies, and
any module outside the package.

## Options

```python
env_settings(package, prefix="", *, empty_as_unset)
```

| Argument | Meaning |
|---|---|
| `package` | Submodules of this package are loaded as settings. Usually `__name__`. |
| `prefix` | Prepended to variable names. With `prefix="APP_"`, `PORT` reads `APP_PORT`. |
| `empty_as_unset` | Required. Whether `NAME=` counts as not set at all. |

`empty_as_unset` has no default on purpose, because it's a decision every project
should make:

| `PORT: int = 8000` with `PORT=` | Result |
|---|---|
| `empty_as_unset=True` | `8000` |
| `empty_as_unset=False` | `RuntimeError`, an empty string isn't a valid `int` |

## Parsing values

Values are parsed as JSON first, then as a plain string, and the result is
validated by pydantic. Any annotation pydantic understands will work:

```python
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr

NAME: str                                 # NAME=hello
RETRIES: Annotated[int, Field(gt=0)] = 3  # RETRIES=5
TIMEOUT: float | None = None              # TIMEOUT=null
LIMITS: dict[str, int] = {}               # LIMITS='{"a": 1}'
DATA_DIR: Path = Path("/var/data")        # DATA_DIR=/srv/data
API_KEY: SecretStr                        # API_KEY=abc123
```

An invalid value raises a `RuntimeError` naming the variable. The value itself is
left out of the message, so that secrets don't end up in logs.

Defaults aren't validated, and they're always evaluated, even if the variable is
set.

## Building on other settings

Settings can import each other, and later ones can use earlier values:

```python
# settings/base.py
PORT: int = 8000
```

```python
# settings/devel.py
from .base import *

URL: str = f"http://localhost:{PORT}"
```

## Selecting settings at runtime

The import inside the block is ordinary Python, so it can be dynamic:

```python
# settings/__init__.py
import os
from importlib import import_module

from pydantic_module_settings import env_settings

with env_settings(__name__, empty_as_unset=True):
    selected = import_module(
        os.environ.get("SETTINGS_MODULE", f"{__name__}.base")
    )
```

```python
import settings

print(settings.selected.PORT)
```

If the block is in a parent package, name the settings package, so that the rest
of the application isn't rewritten:

```python
# app/__init__.py
with env_settings(f"{__name__}.settings", empty_as_unset=True):
    settings = import_module(
        os.environ.get("APP_SETTINGS_MODULE", f"{__name__}.settings.base")
    )
```

## Things to keep in mind

- Settings must live in submodules of a package. A single `settings.py` file, or
  annotated names in the package's own `__init__.py`, aren't rewritten.
- Only load settings inside the block. A settings module first imported after the
  block has ended loads as a regular module and ignores the environment. Modules
  loaded inside the block stay available as usual.
- A selected module outside the package isn't rewritten either, and nothing warns
  about it.
- If a submodule was already imported in another way, entering the block raises a
  `RuntimeError` instead of silently reusing it. That covers regular imports, and
  a different `prefix` or `empty_as_unset`.
- Values are read once, when the module is first imported.

## Development

```shell
uv run invoke static_checks   # format, lint and type check
uv run pytest --cov           # run the tests, requiring 100% coverage
uv run invoke build           # build a wheel and a source distribution
```
