|pypi| |build status| |pyver|

HCLI hst
========

HCLI hst is a python package wrapper that contains an HCLI sample application (hst); hst is an HCLI for playing SpaceTraders via the SpaceTraders API.

----

HCLI hst wraps hst (an HCLI) and is intended to be used with an HCLI Client [1] as presented via an HCLI Connector [2].

You can find out more about HCLI on hcli.io [3]

[1] https://github.com/cometaj2/huckle

[2] https://github.com/cometaj2/hcli_core

[3] http://hcli.io

Installation
------------

HCLI hst requires a supported version of Python and pip.

You'll need an HCLI Connector to run hst. For example, you can use HCLI Core (https://github.com/cometaj2/hcli_core), a WSGI server such as Green Unicorn (https://gunicorn.org/), and an HCLI Client like Huckle (https://github.com/cometaj2/huckle).


.. code-block:: console

    pip install hcli-hst
    pip install hcli-core
    pip install huckle
    pip install gunicorn
    gunicorn --workers=1 --threads=1 -b 127.0.0.1:8000 "hcli_core:connector(\"`hcli_hst path`\")"

Usage
-----

Open a different shell window.

Setup the huckle env eval in your .bash_profile (or other bash configuration) to avoid having to execute eval everytime you want to invoke HCLIs by name (e.g. hst).

Note that no CLI is actually installed by Huckle. Huckle reads the HCLI semantics exposed by the API via HCLI Connector and ends up behaving *like* the CLI it targets.


.. code-block:: console

    huckle cli install http://127.0.0.1:8000
    eval $(huckle env)
    hst help

Versioning
----------

This project makes use of semantic versioning (http://semver.org) and may make use of the "devx",
"prealphax", "alphax" "betax", and "rcx" extensions where x is a number (e.g. 0.3.0-prealpha1)
on github.

Supports
--------

- TBD

To Do
-----

- TBD

Bugs
----

- TBD

.. |build status| image:: https://circleci.com/gh/cometaj2/hcli_hst.svg?style=shield
   :target: https://circleci.com/gh/cometaj2/hcli_hst
.. |pypi| image:: https://img.shields.io/pypi/v/hcli-hst?label=hcli-hst
   :target: https://pypi.org/project/hcli-hst
.. |pyver| image:: https://img.shields.io/pypi/pyversions/hcli-hst.svg
   :target: https://pypi.org/project/hcli-hst
