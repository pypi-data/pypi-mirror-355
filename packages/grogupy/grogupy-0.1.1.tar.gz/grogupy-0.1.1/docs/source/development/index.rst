Contributing to grogupy
=======================

Currently it is more favourable to request new features 
of you want something implemented, but if you really 
want to contribute to the development of grogupy, 
then you can download or fork the repository and once 
you are satisfied with the state of the code you can 
try to merge it. Unfortunately if you choose the second 
option there is no guarantee that your work will be 
implemented in the final product...

Developing new features
-----------------------

To start with the developement first you have to clone 
the repository from Github.

.. code-block:: bash

    git clone https://github.com/danielpozsar/grogu.git

Then the easiest way is to create a a virtual environment (.venv), for
example with VSCode.

* Use at least python 3.9

* install dependencies from:

  * requirements.txt

  * requirements-dev.txt

  * /docs/requirements.txt

Finally you have to install and run ``pre-commit``, which is mainly 
used to automatically format the code to make it nicer and reduce git
differences.

.. code-block:: bash

    pre-commit install
    pre-commit run --all-files

Releasing new version
---------------------

Before releasing you should be sure that pytest runs without 
errors including the benchmarks as well. All new features 
should be documented in both docs and in the relevant 
**__init__.py** files and new tests should be created. The 
example notebooks should be run as well and the documentation 
building should not throw any warnings after removing the 
**_genrated** folder from **API** and running ``make clean``, 
``make build``.

The commit for the version release should not contain any new 
features or bugfixes, just the final steps to update some 
parameters. Here is a list of TODOs in the last commit:

1. Update release version in **CITATION.ciff**
2. Update release date in **CITATION.ciff**
3. Update release version in **__init__.py**
4. Update the changelogs in documentation
5. tag the commit with the proper version number

The packaging and documentation generation is automatically 
done during release by github workflows.