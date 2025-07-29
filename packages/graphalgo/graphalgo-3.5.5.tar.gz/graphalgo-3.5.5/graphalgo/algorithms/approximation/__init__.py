"""Approximations of graph properties and Heuristic methods for optimization.

The functions in this class are not imported into the top-level ``networkx``
namespace so the easiest way to use them is with::

    >>> from graphalgo.algorithms import approximation

Another option is to import the specific function with
``from graphalgo.algorithms.approximation import function_name``.

"""

from graphalgo.algorithms.approximation.clustering_coefficient import *
from graphalgo.algorithms.approximation.clique import *
from graphalgo.algorithms.approximation.connectivity import *
from graphalgo.algorithms.approximation.distance_measures import *
from graphalgo.algorithms.approximation.dominating_set import *
from graphalgo.algorithms.approximation.kcomponents import *
from graphalgo.algorithms.approximation.matching import *
from graphalgo.algorithms.approximation.ramsey import *
from graphalgo.algorithms.approximation.steinertree import *
from graphalgo.algorithms.approximation.traveling_salesman import *
from graphalgo.algorithms.approximation.treewidth import *
from graphalgo.algorithms.approximation.vertex_cover import *
from graphalgo.algorithms.approximation.maxcut import *
from graphalgo.algorithms.approximation.density import *
