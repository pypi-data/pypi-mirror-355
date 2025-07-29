Graphalgo
=========

.. image:: https://github.com/taylortech75/graphalgo/workflows/test/badge.svg?branch=main
   :target: https://github.com/taylortech75/graphalgo/actions?query=workflow%3Atest

.. image:: https://codecov.io/gh/taylortech75/graphalgo/branch/main/graph/badge.svg
   :target: https://app.codecov.io/gh/taylortech75/graphalgo/branch/main

.. image:: https://img.shields.io/pypi/v/graphalgo.svg
   :target: https://pypi.org/project/graphalgo/

.. image:: https://img.shields.io/pypi/l/graphalgo.svg
   :target: https://github.com/taylortech75/graphalgo/blob/main/LICENSE.txt

.. image:: https://img.shields.io/pypi/pyversions/graphalgo.svg
   :target: https://pypi.org/project/graphalgo/

.. image:: https://img.shields.io/github/labels/taylortech75/graphalgo/good%20first%20issue?color=green&label=contribute
   :target: https://github.com/taylortech75/graphalgo/contribute

Graphalgo is a Python package for the creation, manipulation,
and study of the structure, dynamics, and functions
of complex networks.

- **Website (including documentation):** https://networkx.org
- **Mailing list:** https://groups.google.com/forum/#!forum/networkx-discuss
- **Source:** https://github.com/taylortech75/graphalgo
- **Bug reports:** https://github.com/taylortech75/graphalgo/issues
- **Report a security vulnerability:** https://tidelift.com/security
- **Tutorial:** https://networkx.org/documentation/latest/tutorial.html
- **GitHub Discussions:** https://github.com/taylortech75/graphalgo/discussions
- **Discord (Scientific Python):** https://discord.com/invite/vur45CbwMz

Simple example
--------------

Find the shortest path between two nodes in an undirected graph:

.. code:: pycon

    >>> import graphalgo as nx
    >>> G = nx.Graph()
    >>> G.add_edge("A", "B", weight=4)
    >>> G.add_edge("B", "D", weight=2)
    >>> G.add_edge("A", "C", weight=3)
    >>> G.add_edge("C", "D", weight=4)
    >>> nx.shortest_path(G, "A", "D", weight="weight")
    ['A', 'B', 'D']

Install
-------

Install the latest released version of Graphalgo:

.. code:: shell

    pip install graphalgo

Install with all optional dependencies:

.. code:: shell

    pip install graphalgo[default]

For additional details,
please see the `installation guide <https://networkx.org/documentation/stable/install.html>`_.

Bugs
----

Please report any bugs that you find `here <https://github.com/taylortech75/graphalgo/issues>`_.
Or, even better, fork the repository on `GitHub <https://github.com/taylortech75/graphalgo>`_
and create a pull request (PR). We welcome all changes, big or small, and we
will help you make the PR if you are new to `git` (just ask on the issue and/or
see the `contributor guide <https://networkx.org/documentation/latest/developer/contribute.html>`_).

License
-------

Released under the `3-clause BSD license <https://github.com/taylortech75/graphalgo/blob/main/LICENSE.txt>`_::

    Copyright (c) 2004-2025, Graphalgo Developers
    Your Name <your@email.com>
