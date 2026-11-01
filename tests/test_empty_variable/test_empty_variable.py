from importlib import import_module

from helpers import with_env


@with_env({"FOO_VALUE": ""})
def test_empty_prefixed_variable_counts_as_unset_when_enabled():
    assert import_module(".package.unset", __package__).VALUE == 5


@with_env({"TEXT": ""})
def test_empty_variable_stays_empty_when_disabled():
    assert import_module(".package.kept", __package__).TEXT == ""
