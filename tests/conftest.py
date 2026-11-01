import sys

import pytest


@pytest.fixture(autouse=True)
def forget_packages():
    """Lets every test import its package from scratch."""
    meta_path = list(sys.meta_path)
    yield
    sys.meta_path[:] = meta_path
    for name in list(sys.modules):
        root, *rest = name.split(".")
        if root.startswith("test_") and rest[:1] == ["package"]:
            del sys.modules[name]
