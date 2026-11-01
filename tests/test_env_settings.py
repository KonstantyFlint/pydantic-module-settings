import sys
import types
from importlib.machinery import ModuleSpec, PathFinder, SourcelessFileLoader

import pytest

from pydantic_env_settings import env_settings
from pydantic_env_settings.import_machinery import EnvSettingsFinder, LoadOptions


def test_empty_as_unset_decision_is_required():
    with pytest.raises(TypeError, match="empty_as_unset"):
        env_settings("settings")


def test_empty_as_unset_cannot_be_positional():
    with pytest.raises(TypeError):
        env_settings("settings", "", True)


@pytest.mark.parametrize(
    "spec",
    [
        None,
        ModuleSpec("unknown_loader.base", None),
        ModuleSpec(
            "unknown_loader.base",
            SourcelessFileLoader("unknown_loader.base", "base.pyc"),
        ),
    ],
)
def test_unknown_loader_raises(monkeypatch, spec):
    module = types.ModuleType("unknown_loader.base")
    module.__spec__ = spec
    monkeypatch.setitem(sys.modules, "unknown_loader.base", module)

    with (
        pytest.raises(RuntimeError, match=r"differently: unknown_loader\.base\.$"),
        env_settings("unknown_loader", empty_as_unset=False),
    ):
        pass


def test_finder_target_defaults_to_none(monkeypatch):
    calls = []
    monkeypatch.setattr(PathFinder, "find_spec", lambda *args: calls.append(args))

    EnvSettingsFinder("settings", LoadOptions("", False)).find_spec(
        "settings.base", None
    )

    assert calls == [("settings.base", None, None)]
