.. :changelog:

History
-------

0.0.1 (2018-10-23)
------------------

* First release on PyPI.

0.0.2 (2018-11-09)
------------------

* Second release on PyPI.
* Created Skeleton of the command line Interface.

0.0.3 (2023-10-18)
------------------

* Implemented data store in home directory. 
* Made project commands functional.

0.0.4 (2023-10-28)
------------------

* Implemented state.
* Improved project commands.

0.0.5 (2023-10-30)
------------------

* Made task commands functional.
* Improved project summary.
* Project summary now shows total duration of the project.

0.0.6 (2023-10-31)
------------------

* bug fix
* readme and doc update
* Improved Command line interface outputs.

0.0.7 (2023-11-01)
------------------

* Added show sub command for project.
* Added json sub command for project.
* refactored project and task commands output messages.
* fixed bugs in project sub commands.

0.0.8 (2023-11-01)
------------------

* Added config sub command.
* added command to save default user information.
* refactored project and task commands.
* fixed bugs.
* added config command to configure project meta data such as title, billable? etc.
  
0.0.9 (2023-11-02)
------------------

* Added config invoice command for configuring default invoice texts and logo.
* Added invoice sub command.
* Added invoice manual command to generate manual invoice using prompts.
* Added invoice auto <Project> command to generate invoice from existing projects.
* invoice manual and auto command generates HTML invoices using Tailwind CSS and opens it in a Browser.

0.0.10 (2023-11-03)
-------------------

* open invoices using python's standard library.
* code refactor
* bug fix

0.0.11 (2023-11-03)
-------------------

* Major bug fix.

0.0.12 (2023-11-04)
-------------------

* Bug fix.

0.0.13 (2023-11-07)
-------------------

* Made the init command optional.

0.0.14 (2023-11-07)
-------------------

* config invoice command bug fix.
* copy logo instead of moving it permanently when configuring invoice.
* fixed f strings quote issue.
* made init command hidden.
* improved doc strings and help texts.