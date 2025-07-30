import graphex as nx
import graphex.algorithms.approximation as a


def test_min_maximal_matching():
    # smoke test
    G = nx.Graph()
    assert len(a.min_maximal_matching(G)) == 0
