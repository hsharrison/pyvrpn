============
pyvrpn [WIP]
============

High-level Python interface between the `VRPN`_ project and `pyglet`_.

+--------------------+-------------------+---------------+
| | |travis-badge|   | | |version-badge| | | |git-badge| |
| | |coverage-badge| | | |license-badge| | | |hg-badge|  |
+--------------------+-------------------+---------------+

.. |travis-badge| image:: http://img.shields.io/travis/hsharrison/pyvrpn.png?style=flat
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/hsharrison/pyvrpn

.. |coverage-badge| image:: http://img.shields.io/coveralls/hsharrison/pyvrpn.png?style=flat
    :alt: Coverage Status
    :target: https://coveralls.io/r/hsharrison/pyvrpn

.. |version-badge| image:: http://img.shields.io/pypi/v/pyvrpn.png?style=flat
    :alt: PyPi Package
    :target: https://pypi.python.org/pypi/pyvrpn

.. |license-badge| image:: http://img.shields.io/badge/license-MIT-blue.png?style=flat
    :alt: License
    :target: https://pypi.python.org/pypi/pyvrpn

.. |git-badge| image:: http://img.shields.io/badge/repo-git-lightgrey.png?style=flat
    :alt: Git Repository
    :target: https://github.com/hsharrison/pyvrpn

.. |hg-badge| image:: http://img.shields.io/badge/repo-hg-lightgrey.png?style=flat
    :alt: Mercurial Repository
    :target: https://bitbucket.org/hharrison/pyvrpn

This package provides a pure-Python interface to the `VRPN`_ library, for interfacing with virtual reality hardware.
Whereas existing Python bindings for `VRPN`_  only interface with the client side, ``pyvrpn`` allows the user to start and stop the server process, dynamically constructing the server configuration based on the receivers that are in use.

``pyvrpn`` implements receivers as subclasses of `pyglet`_ `event dispatchers`_.
They dispatch an event called ``on_receiver_input`` when new data is received.
Register an event handler for this event to respond to incoming receiver data.

Installation
============

Only Python versions >= 3.4 is supported.
Installing with ``pip`` is recommended::

    pip install pyvrpn --upgrade

The Python package `pyglet`_ is required; only version 1.2 is supported.
This is only available in alpha, which is not on PyPi.
It can be installed from source from its Mercurial repository at ``http://code.google.com/p/pyglet``.

Additionally, the `VRPN`_ library is required, as is its included low-level Python interface (the one in the ``python`` directory, not the ``vrpn_python`` directory).
This dependency has been conveniently packaged as a `conda`_ environment, under the name ``vrpn``, and uploaded to the `binstar`_ channel ``hharrison``.

Finally, the Python package `toolz`_ or its Cythonized stand-in `cytoolz`_ is required.

The easiest way to install `conda`_ is with `Miniconda`_.
From there, the following will create a new ``conda`` environment named ``'vr'`` and install Python 3.4, ``vrpn``, ``pyglet``, and ``pyvrpn``::

    conda create -n vr python=3.4 pip
    conda install -n vr vrpn -c hharrison
    source activate vr
    pip install hg+http://code.google.com/p/pyglet#egg=pyglet
    pip install pyvrpn

VRPN builds
-----------

Currently, the only builds of ``vrpn`` on `binstar`_ are for ``pc_linux64`` architecture, for Python 2.7, 3.3, and 3.4.
They are compiled with LibUSB, which can be installed on Debian-based systems with ``sudo apt-get install libusb-1.0-0``.

The ``vrpn`` `build_recipe`_ is available on BitBucket.
The file ``compile.patch`` may be of use for anyone attempting to manually build ``vrpn`` or edit the build recipe for a different system or configuration.

Documentation
=============

https://pyvrpn.readthedocs.org/

Development
===========

To run the all tests run::

    tox

.. _VRPN: http://www.cs.unc.edu/Research/vrpn/
.. _conda: http://conda.pydata.org/docs/
.. _Miniconda: http://conda.pydata.org/miniconda.html
.. _binstar: https://binstar.org/
.. _build recipe: https://bitbucket.org/hharrison/conda-vrpn-recipe
.. _pyglet: http://www.pyglet.org/
.. _event dispatchers: http://www.pyglet.org/doc-current/programming_guide/events.html#creating-your-own-event-dispatcher
.. _cytoolz: https://github.com/pytoolz/cytoolz
.. _toolz: http://toolz.readthedocs.org/en/latest/
