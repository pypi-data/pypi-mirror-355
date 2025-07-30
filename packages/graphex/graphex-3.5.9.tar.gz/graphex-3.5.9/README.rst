Graphex
=======

.. image:: https://img.shields.io/pypi/v/graphex.svg
   :target: https://pypi.org/project/graphex/

.. image:: https://img.shields.io/pypi/l/graphex.svg
   :target: https://github.com/taylortech75/graphex/blob/main/LICENSE.txt

.. image:: https://img.shields.io/pypi/pyversions/graphex.svg
   :target: https://pypi.org/project/graphex/

.. image:: https://img.shields.io/github/labels/taylortech75/graphex/good%20first%20issue?color=green&label=contribute
   :target: https://github.com/taylortech75/graphex/contribute

**Graphex** is a Python package for the creation, manipulation, and study of the structure, dynamics, and functions of complex networks.

Resources
---------

- **Website (including documentation):** https://networkx.org
- **Mailing list:** https://groups.google.com/forum/#!forum/networkx-discuss
- **Source:** https://github.com/taylortech75/graphex
- **Bug reports:** https://github.com/taylortech75/graphex/issues
- **Report a security vulnerability:** https://tidelift.com/security
- **Tutorial:** https://networkx.org/documentation/latest/tutorial.html
- **GitHub Discussions:** https://github.com/taylortech75/graphex/discussions
- **Discord (Scientific Python):** https://discord.com/invite/vur45CbwMz

Simple Example
--------------

Find the shortest path between two nodes in an undirected graph:

.. code:: pycon

    >>> import graphex as nx
    >>> G = nx.Graph()
    >>> G.add_edge("A", "B", weight=4)
    >>> G.add_edge("B", "D", weight=2)
    >>> G.add_edge("A", "C", weight=3)
    >>> G.add_edge("C", "D", weight=4)
    >>> nx.shortest_path(G, "A", "D", weight="weight")
    ['A', 'B', 'D']

Install
-------

Install the latest released version of Graphex:

.. code:: shell

    pip install graphex

Install with all optional dependencies:

.. code:: shell

    pip install graphex[default]

For additional details, please see the `installation guide <https://networkx.org/documentation/stable/install.html>`_.

Bugs
----

Please report any bugs `here <https://github.com/taylortech75/graphex/issues>`_.
Even better, fork the repository on `GitHub <https://github.com/taylortech75/graphex>`_ and create a pull request (PR).
We welcome all contributions, big or small, and we will help you make the PR if you're new to `git`.
Just ask on the issue and/or see the `contributor guide <https://networkx.org/documentation/latest/developer/contribute.html>`_.

License
-------

Released under the `3-clause BSD license <https://github.com/taylortech75/graphex/blob/main/LICENSE.txt>`_::

    Copyright (c) 2004–2025, graphex Developers
    Your Name <your@email.com>
