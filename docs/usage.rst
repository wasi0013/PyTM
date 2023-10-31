=====
Usage
=====

For installation information Checkout: `this instruction <installation.html>`_

Basic commands:
---------------

Currently available commands are listed below:

Commands related to project
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Start a new/existing project::

    pytm project start PROJECT_NAME

* Remove a project::

    pytm project remove PROJECT_NAME

* Check status of a project::

    pytm project status PROJECT_NAME

* Check summary of a project::

    pytm project summary PROJECT_NAME

* Finish active project::

    pytm project finish

* Pause active project::

    pytm project pause

* Abort active project::

    pytm project abort

Commands related to Task
~~~~~~~~~~~~~~~~~~~~~~~~

* Start a new or existing task in the current active project::

    pytm task start TASK_NAME

* Remove a task::

    pytm task remove TASK_NAME

* current task's status::

    pytm task status

* Finish active task::

    pytm task finish

* Pause active task::

    pytm task pause

* Abort active task::

    pytm task abort

Others
~~~~~~
Check version::

    pytm --version
    pytm -v


For a list of all the available options or, arguments try::

    pytm --help
