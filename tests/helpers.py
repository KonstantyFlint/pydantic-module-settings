import os
from functools import partial
from unittest.mock import patch

# Replaces the whole environment with the given dict, as a decorator or a context
# manager, so a test's environment is exactly what it lists.
with_env = partial(patch.dict, os.environ, clear=True)
