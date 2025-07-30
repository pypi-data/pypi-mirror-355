Introduction
============
grogupy is a package that contains a variety of modules to calculate and 
visualize magnetic interaction parameters. One of the main features is the 
ability to calculate the magnetic anisotropy as well from relativistic 
calculations.

.. math::

    H(\{\vec{e}_i\}) = \frac{1}{2} \sum_{i \neq j} \vec{e_i} J_{ij} \vec{e_j} + 
    \sum_{i} \vec{e_i} K_{i} \vec{e_i}


It can also be used to set up more complex convergence and high throughput
calculations.

1. grogupy can efficiently calculate the magnetic interaction parameters of a 
large number of atoms or magnetic entites. The most resource consuming part of 
the simulation is the Green's function calculation, but the number of matrix 
inversions does not depend on the number of pairs in the system, so the increase 
in the number of pairs is very cheap computationally.

2. It is capable to visualize the examined system including the calculated 
magnetic parameters, like the isotropic, symmetric and antisymmetric exchange 
or the Dzyaloshinskii-Morilla  vectors.

3. It is capable to carry out automatic convergence test and create workflows 
for high throughput calculations.

Package
-------

grogupy is a Python package that can calculate and visualize magnetic
interaction parameters. It can be run in a juptyer notebook or in a command 
line interface with the ability of GPU acceleration.

Go to the :ref:`installation <quickstart-guide>` page to install grogupy.

Command line usage
------------------

grogupy contains  :ref:`command line scripts <command_line_usage>` to run 
simulations and to create automatic summaries of the output files. Currently 
there is no way to run automatic convergence tests, because the total runtime 
and required resources are hardware dependent and hard to estimate. Instead 
there are functions in the ``viz`` module that helps the user determine the 
convergence from multiple runs.
