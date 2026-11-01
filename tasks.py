import shutil

from invoke.context import Context
from invoke.tasks import task

PACKAGE = "pydantic_module_settings"


@task
def static_checks(c: Context) -> None:
    """Format and lint with ruff, then check types with mypy."""
    c.run("ruff format .", pty=False)
    c.run("ruff check --fix .", pty=False)
    c.run(f"mypy --strict {PACKAGE}", pty=False)
    c.run(f"mypy {PACKAGE} tests tasks.py", pty=False)


@task
def build(c: Context) -> None:
    """Build a wheel and a source distribution into a clean dist/."""
    shutil.rmtree("dist", ignore_errors=True)
    c.run("uv build", pty=False)
