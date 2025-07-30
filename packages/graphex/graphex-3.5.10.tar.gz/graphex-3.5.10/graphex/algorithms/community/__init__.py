"""Functions for computing and measuring community structure.

The ``community`` subpackage can be accessed by using :mod:`networkx.community`, then accessing the
functions as attributes of ``community``. For example::

    >>> import graphex as nx
    >>> G = nx.barbell_graph(5, 1)
    >>> communities_generator = nx.community.girvan_newman(G)
    >>> top_level_communities = next(communities_generator)
    >>> next_level_communities = next(communities_generator)
    >>> sorted(map(sorted, next_level_communities))
    [[0, 1, 2, 3, 4], [5], [6, 7, 8, 9, 10]]

"""

from graphex.algorithms.community.asyn_fluid import *
from graphex.algorithms.community.centrality import *
from graphex.algorithms.community.divisive import *
from graphex.algorithms.community.kclique import *
from graphex.algorithms.community.kernighan_lin import *
from graphex.algorithms.community.label_propagation import *
from graphex.algorithms.community.lukes import *
from graphex.algorithms.community.modularity_max import *
from graphex.algorithms.community.quality import *
from graphex.algorithms.community.community_utils import *
from graphex.algorithms.community.louvain import *
from graphex.algorithms.community.leiden import *
from graphex.algorithms.community.local import *
