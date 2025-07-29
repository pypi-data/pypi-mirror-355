"""
graphalgo
========

graphalgo is a Python package for the creation, manipulation, and study of the
structure, dynamics, and functions of complex networks.

See https://graphalgo.org for complete documentation.
"""

__version__ = "3.5.2"


# These are imported in order as listed
from graphalgo.lazy_imports import _lazy_import

from graphalgo.exception import *

from graphalgo import utils
from graphalgo.utils import _clear_cache, _dispatchable

# load_and_call entry_points, set configs
config = utils.backends._set_configs_from_environment()
utils.config = utils.configs.config = config  # type: ignore[attr-defined]

from graphalgo import classes
from graphalgo.classes import filters
from graphalgo.classes import *

from graphalgo import convert
from graphalgo.convert import *

from graphalgo import convert_matrix
from graphalgo.convert_matrix import *

from graphalgo import relabel
from graphalgo.relabel import *

from graphalgo import generators
from graphalgo.generators import *

from graphalgo import readwrite
from graphalgo.readwrite import *

# Need to test with SciPy, when available
from graphalgo import algorithms
from graphalgo.algorithms import *

from graphalgo import linalg
from graphalgo.linalg import *

from graphalgo import drawing
from graphalgo.drawing import *


def __getattr__(name):
    if name == "random_tree":
        raise AttributeError(
            "nx.random_tree was removed in version 3.4. Use `nx.random_labeled_tree` instead.\n"
            "See: https://graphalgo.org/documentation/latest/release/release_3.4.html"
        )
    raise AttributeError(f"module 'graphalgo' has no attribute '{name}'")
