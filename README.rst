 .. image:: https://github.com/wasi0013/PyTM/raw/master/ext/images/PyTM-logo.png
    :target: https://github.com/wasi0013/PyTM/
    :alt: PyTM - Logo




**PУΓM** -  A CLI time tracker for projects with invoice generation
-------------------------------------------------------------------


|image1| |image2| |image3| |Contributors| |DownloadStats| |DocsStats|
=====================================================================

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
   :target: https://pytm.readthedocs.io/en/latest/?badge=latest
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

You can download it from `PyPI <https://pypi.org/project/python-pytm/>`_ using :code:`pip`::

    python -m pip install python-pytm

Check the version by typing the following in your terminal.::
    
     pytm --version


Basic commands
---------------

To see the available commands type::

    pytm --help


Commands related to projects
============================

* Start a new/existing project: :code:`pytm project start PROJECT_NAME`
* Remove a project: :code:`pytm project remove PROJECT_NAME`
* Check the status of a project: :code:`pytm project status PROJECT_NAME`
* Check the list of tasks and duration of a project: :code:`pytm project summary PROJECT_NAME`
* Finish active project: :code:`pytm project finish`
* Pause active project: :code:`pytm project pause`
* Abort active project: :code:`pytm project abort`

Commands related to Task
========================

* Start a new or existing task in the current active project: :code:`pytm task start TASK_NAME`
* Remove a task: :code:`pytm task remove TASK_NAME`
* current task's status: :code:`pytm task status`
* Finish active task: :code:`pytm task finish`
* Pause active task: :code:`pytm task pause`
* Abort active task: :code:`pytm task abort`

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


For a list of all the available commands try::

    pytm --help


Running the tests
-----------------

* Clone this `repository <https://github.com/wasi0013/PyTM>`_

* Install dependencies::

    pip install -r requirements.txt

* run the tests::

    py.test


Notes
-----

* **Author** - `Wasi <https://www.wasi0013.com/>`_ - (`wasi0013 <https://github.com/wasi0013>`_).
* **License** - see the `LICENSE <LICENSE>`_ file.
* **Contributing** - see `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ for detail. You can also help by creating `issues <https://github.com/wasi0013/PyTM/issues/new/>`_.
* **Version** - see the `tags on this repository <https://github.com/wasi0013/PyTM/tags>`_.
* **Acknowledgments** - bootstrapped using `this cookiecutter package <https://github.com/audreyr/cookiecutter-pypackage>`_.
* Built With :heart: using `Python <https://python.org/>`_.
