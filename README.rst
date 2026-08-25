 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/PyTM-logo.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Logo




**PyTM** -  A CLI time tracker for projects with invoice generation
-------------------------------------------------------------------


|image1| |coverage| |image3| |Contributors| |DownloadStats| |DocsStats| |image2|
================================================================================

.. |image1| image:: https://badge.fury.io/py/python-pytm.png
   :target: https://badge.fury.io/py/python-pytm
.. |image2| image:: https://img.shields.io/pypi/l/python-pytm.svg
   :target: https://pypi.org/project/python-pytm/
.. |image3| image:: https://img.shields.io/pypi/pyversions/python-pytm.svg
   :target: https://pypi.org/project/python-pytm/
   :alt: Supported Python Versions
.. |Contributors| image:: https://img.shields.io/github/contributors/wasi0013/PyTM.svg
   :target: https://github.com/wasi0013/PyTM/graphs/contributors
   :alt: List of Contributors
.. |DownloadStats| image:: https://pepy.tech/badge/python-pytm
   :target: https://pepy.tech/project/python-pytm
   :alt: Download Stats
.. |DocsStats| image:: https://readthedocs.org/projects/pytm/badge/?version=latest
   :target: https://pytm.readthedocs.io/
   :alt: Documentation Status
.. |coverage| image:: https://img.shields.io/badge/coverage-84%25-blue
   :target: https://pytm.readthedocs.io/
   :alt: Documentation Status

Goals
-----

Project time management, billing, and invoice generation.

Preview
-------

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.gif
    :target: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.gif
    :alt: PyTM - Preview

Screenshots
-----------

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/demo.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Screenshot

 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/Demo-Invoice.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Invoice

Installing PyTM
---------------

PyTM is installed with `uv <https://docs.astral.sh/uv/>`_, a fast, single-binary
Python package manager. It takes care of getting a suitable Python version for
you too, so there's nothing else to install first.

* Install uv (skip this if you already have it)::

    curl -LsSf https://astral.sh/uv/install.sh | sh

  Windows, and other install options, are covered in the
  `uv installation docs <https://docs.astral.sh/uv/getting-started/installation/>`_.

* Install PyTM as a standalone command-line tool::

    uv tool install python-pytm

  This puts a ``pytm`` command on your ``PATH``, isolated in its own
  environment, without touching any other Python project on your machine.

  Prefer not to install anything permanently? Try it in one shot instead::

    uvx python-pytm --help

Check the version by typing the following in your terminal.::

     pytm --version


Basic commands
---------------

To see the available commands type::

    pytm --help


Commands related to projects
============================
* Start a new project with a default name: :code:`pytm project start`
* Start a new project with the given name or, start an existing project: :code:`pytm project start PROJECT_NAME`
* Rename a project: :code:`pytm project rename OLD_PROJECT_NAME NEW_NAME`
* Remove a project: :code:`pytm project remove PROJECT_NAME`
* Check the status of a project: :code:`pytm project status PROJECT_NAME`
* Check the list of tasks and duration of a project: :code:`pytm project summary PROJECT_NAME`
* Finish active project: :code:`pytm project finish`
* Pause active project: :code:`pytm project pause`
* Abort active project: :code:`pytm project abort`

Commands related to Task
========================
* Start a new task with a default name in the current active project: :code:`pytm task start`
* Start a new task with the given name or existing task in the current active project: :code:`pytm task start TASK_NAME`
* Rename a task of the active project: :code:`pytm task rename OLD_TASK_NAME NEW_NAME`
* Remove a task: :code:`pytm task remove TASK_NAME`
* current task's status: :code:`pytm task status`
* Finish active task: :code:`pytm task finish`
* Pause active task: :code:`pytm task pause`
* Abort active task: :code:`pytm task abort`
* Atomically pause the active task and start/resume another: :code:`pytm task switch TASK_NAME`
* Correct a task's recorded duration by hand: :code:`pytm task edit TASK_NAME --duration HOURS`

Time digests
============
* Time logged today, across all projects: :code:`pytm today`
* Time logged this week, across all projects: :code:`pytm week`
* The week's start day (default Saturday) is configurable: :code:`pytm config user --week-start monday`

Ambient tracking (shell hooks)
===============================
Automatically start/switch tasks based on the directory you `cd` into and the
git branch you're on — opt-in, per directory, no auto-detection.

* Link a directory (and its subdirectories) to a project::

    cd ~/code/my-client-project
    pytm hook link my-client-project

* Enable the hook in your shell rc file (``~/.bashrc`` or ``~/.zshrc``)::

    eval "$(pytm hook init bash)"   # or: pytm hook init zsh

  From then on, `cd`-ing into a linked directory (or any of its
  subdirectories) starts/resumes its project, and switching git branch
  there switches to a task named after the branch. Directories that were
  never linked are left untouched — nothing is inferred automatically.

* Manage links: :code:`pytm hook list`, :code:`pytm hook unlink`
* See what a directory would resolve to without applying it: :code:`pytm hook resolve`

Backup (git-based, local by default)
=====================================
Turns ``~/.pytm`` into its own git repo and commits every write
automatically. Opt-in and commit-only by default — no remote is
configured or pushed to unless you explicitly ask.

* Turn it on::

    pytm backup enable

* Check status (enabled/disabled, working-tree clean/dirty, last commit,
  configured remote)::

    pytm backup status

* Point it at a remote you control (a private GitHub/GitLab repo, or any
  git host, including self-hosted) — this only configures the remote, it
  doesn't push::

    pytm backup remote set git@github.com:you/pytm-backup.git

* Push manually when you want an off-site copy. Auto-backup never pushes
  on its own — it only commits locally::

    pytm backup push

* Manually flush any pending changes (works whether auto-backup is on or
  off)::

    pytm backup commit

* Turn it off (history and any configured remote are left untouched)::

    pytm backup disable

**Restoring on a new machine** (after a lost/stolen laptop, say) is a
plain git clone — there's no separate ``pytm backup restore`` command,
because none is needed::

    git clone git@github.com:you/pytm-backup.git ~/.pytm

If you never configured a remote, commit-only backup protects against a
corrupted write or an accidental ``rm``, but not against losing the
machine itself — run ``pytm backup remote set`` and ``pytm backup push``
if you want that guarantee too.

Others
======
Configure project, user and invoice info::

    pytm config project PROJECT_NAME
    pytm config user
    pytm config invoice

Generate Invoice::
    
    pytm invoice auto PROJECT_NAME
    pytm invoice manual

Check version::

    pytm --version
    pytm -v

Check summary of all the projects::

    pytm summary

For a list of all the available commands try::

    pytm --help


Running the tests
-----------------

This is for working on PyTM itself, not for just using it — if you only want
the ``pytm`` command, see `Installing PyTM`_ above instead.

* Clone this `repository <https://github.com/wasi0013/PyTM>`_ and ``cd`` into it::

    git clone https://github.com/wasi0013/PyTM.git
    cd PyTM

* Create a virtual environment (uv downloads a matching Python for you if
  needed) and install dependencies into it::

    uv venv
    uv pip install -r requirements.txt

* Run the tests::

    uv run pytest

  ``uv run`` finds the ``.venv`` created above automatically, so there's no
  need to manually activate it first.


Notes
-----

* **Author** - `Wasi <https://www.wasi0013.com/>`_ - (`wasi0013 <https://github.com/wasi0013>`_).
* **License** - see the `LICENSE <LICENSE>`_ file.
* **Contributing** - see `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ for detail. You can also help by creating `issues <https://github.com/wasi0013/PyTM/issues/new/>`_.
* **Version** - see the `tags on this repository <https://github.com/wasi0013/PyTM/tags>`_.
* **Acknowledgments** - bootstrapped using `this cookiecutter package <https://github.com/audreyr/cookiecutter-pypackage>`_.
* Built With :heart: using `Python <https://python.org/>`_.
