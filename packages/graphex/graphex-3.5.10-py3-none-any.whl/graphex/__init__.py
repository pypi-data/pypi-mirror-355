"""
graphex
========

graphex is a Python package for the creation, manipulation, and study of the
structure, dynamics, and functions of complex networks.

See https://graphex.org for complete documentation.
"""

__version__ = "3.5.10"


# These are imported in order as listed
from graphex.lazy_imports import _lazy_import

from graphex.exception import *

from graphex import utils
from graphex.utils import _clear_cache, _dispatchable

# load_and_call entry_points, set configs
config = utils.backends._set_configs_from_environment()
utils.config = utils.configs.config = config  # type: ignore[attr-defined]

from graphex import classes
from graphex.classes import filters
from graphex.classes import *

from graphex import convert
from graphex.convert import *

from graphex import convert_matrix
from graphex.convert_matrix import *

from graphex import relabel
from graphex.relabel import *

from graphex import generators
from graphex.generators import *

from graphex import readwrite
from graphex.readwrite import *

# Need to test with SciPy, when available
from graphex import algorithms
from graphex.algorithms import *

from graphex import linalg
from graphex.linalg import *

from graphex import drawing
from graphex.drawing import *


def __getattr__(name):
    if name == "random_tree":
        raise AttributeError(
            "nx.random_tree was removed in version 3.4. Use `nx.random_labeled_tree` instead.\n"
            "See: https://graphex.org/documentation/latest/release/release_3.4.html"
        )
    raise AttributeError(f"module 'graphex' has no attribute '{name}'")
