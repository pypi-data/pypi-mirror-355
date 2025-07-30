"""Approximations of graph properties and Heuristic methods for optimization.

The functions in this class are not imported into the top-level ``networkx``
namespace so the easiest way to use them is with::

    >>> from graphex.algorithms import approximation

Another option is to import the specific function with
``from graphex.algorithms.approximation import function_name``.

"""

from graphex.algorithms.approximation.clustering_coefficient import *
from graphex.algorithms.approximation.clique import *
from graphex.algorithms.approximation.connectivity import *
from graphex.algorithms.approximation.distance_measures import *
from graphex.algorithms.approximation.dominating_set import *
from graphex.algorithms.approximation.kcomponents import *
from graphex.algorithms.approximation.matching import *
from graphex.algorithms.approximation.ramsey import *
from graphex.algorithms.approximation.steinertree import *
from graphex.algorithms.approximation.traveling_salesman import *
from graphex.algorithms.approximation.treewidth import *
from graphex.algorithms.approximation.vertex_cover import *
from graphex.algorithms.approximation.maxcut import *
from graphex.algorithms.approximation.density import *
