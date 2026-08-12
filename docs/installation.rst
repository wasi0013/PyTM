===============
Installing PyTM
===============

PyTM is installed with `uv <https://docs.astral.sh/uv/>`_, a fast, single-binary
Python package manager. If you don't have it yet::

    curl -LsSf https://astral.sh/uv/install.sh | sh

(see the `uv installation docs <https://docs.astral.sh/uv/getting-started/installation/>`_
for Windows and other options.)

Then install PyTM as a standalone command-line tool::

    uv tool install python-pytm

Or try it without installing anything::

    uvx python-pytm --help

Checkout the version by typing the following in your terminal/command prompt::

    pytm --version


For a list of all the available options or, arguments try::

    pytm --help
