Welcome to pygments-tldr
===================

This is the source of pygments-tldr.  This is a fork of the excellent pygments project that can be found at
https://pygments.org/.  We created this fork to support a new type of formatter we have added to the pygments
project that helps us extract function signatures from multiple programming language files.  We have tried to
contain our impactful changes to the file ''pygments_tldr/formatters/tldr.py''.  Everything else we will strive to keep
up to date and in sync with the original pygments project.  Eventually we would like to merge this back into the
original pygments project, if the maintainers of that project are interested in our changes.

Installing
----------

... works as usual, use ``pip install pygments-tldr`` to get published versions,
or ``pip install -e .`` to install from a checkout in editable mode.

Documentation
-------------

Documentation for the original pygments project can be found online at https://pygments.org/ or created with Sphinx by ::

   tox -e doc

By default, the documentation does not include the demo page, as it requires
having Docker installed for building Pyodide. To build the documentation with
the demo page, use ::

   tox -e web-doc

The initial build might take some time, but subsequent ones should be instant
because of Docker caching.

To view the generated documentation, serve it using Python's ``http.server``
module (this step is required for the demo to work) ::

   python3 -m http.server --directory doc/_build/html
