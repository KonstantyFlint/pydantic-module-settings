import importlib
import sys
from importlib import import_module

import pytest
from helpers import with_env


@pytest.mark.parametrize(
    "case", ["different_prefix", "dropped_prefix", "different_empty_as_unset"]
)
def test_mismatched_options_raise(case):
    with pytest.raises(RuntimeError, match=rf"differently: .*{case}\.base\.$"):
        import_module(f".package.{case}", __package__)


@with_env({"FOO_VALUE": "2"})
def test_same_options_can_be_used_again():
    assert import_module(".package.same_prefix", __package__).base.VALUE == 2


def test_dependency_imported_before_block_raises():
    with pytest.raises(RuntimeError, match=r"differently: .*preloaded\.base\.$"):
        import_module(".package.preloaded", __package__)

    assert f"{__package__}.package.preloaded.devel" not in sys.modules


@with_env({})
def test_reloading_allows_namespace_subpackage():
    settings = import_module(".package.namespace", __package__)

    assert importlib.reload(settings).VALUE == 1
