.. _quickstart-guide:

Quickstart
==========

Installation
------------
.. grid:: 1 2 2 2
    :gutter: 4

    .. grid-item-card:: Using pip
        :columns: 12 12 12 12

        grogupy can be quickly installed via pip from 
        `PyPI <https://pypi.org>`_.

        ++++

        .. code-block:: bash

            pip install grogupy

        The plotting, MPI acceleration and GPU aceleration part of the 
        package are optional, but they can also be download via pip.

        .. code-block:: bash

            pip install grogupy[viz,gpu,mpi]


    .. grid-item-card:: Using source code
        :columns: 12 12 12 12

        Or if you want to use the latest development version, first go to an 
        empty directory and clone the git repository. Then you can build the 
        wheel and install with pip.

        ++++

        .. code-block:: bash

            git clone https://github.com/danielpozsar/grogupy.git
            python -m build
            pip install dist/grogupy-VERSION_NUMBER-py3-none-any



Quickstart tutorials
--------------------

.. toctree::
   :maxdepth: 1

   calculate_magnetic_parameters.ipynb
   visualize_the_exchange.ipynb
   running_in_hpc
