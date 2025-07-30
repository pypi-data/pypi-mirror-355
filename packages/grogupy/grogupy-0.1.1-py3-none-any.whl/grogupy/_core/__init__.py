# Copyright (c) [2024-2025] [Grogupy Team]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Core
====

.. currentmodule:: grogupy._core

This subpackage contains the core functionalities including mathematical 
function, and important class methods from all over the main package.

Constants
---------

Here are the physical constants and default values for the input.

Cpu solvers
-----------

Functions used in the solution method of the ``Builder`` class.
Parallelization is done using MPI if it is available.

.. autosummary::
   :toctree: _generated/

   default_solver          It calculates the energies by the Greens function method without MPI parallelization.
   solve_parallel_over_k   It calculates the energies by the Greens function method with parallelization over k points.


Gpu solvers
-----------

Functions used in the solution method of the ``Builder`` class.
Because GPUs run asyncronusly, we can unlock the GIL in python
and run in a parallel manner over multiple GPUs. The only constrain
is the input/output writing between hardwares.

.. autosummary::
   :toctree: _generated/

   solve_parallel_over_k        It calculates the energies by the Greens function method.
   gpu_solver                   Parallelizes the Green's function solution on GPU.

Utilities
---------

Miscellaneous suport functions used around the code. There are mathematical functions, 
``Contour``, ``Kspace`` and ``Hamiltonian`` methods, magnetic entity and pair generation.

.. autosummary::
   :toctree: _generated/

   commutator                   Shorthand for commutator.
   tau_u                        Pauli matrix in direction u.
   crossM                       Definition for the cross-product matrix.
   RotM                         Definition of rotation matrix with angle theta around direction u.
   RotMa2b                      Definition of rotation matrix rotating unit vector a to unit vector b.
   setup_from_range             Generates all the pairs and magnetic entities from atoms in a given radius.
   arrays_lists_equal           Compares two objects with specific rules.
   arrays_None_equal            Compares two objects with specific rules.
   onsite_projection            It produces the slices of a matrix for the on site projection.
   calc_Vu                      Calculates the local perturbation in case of a spin rotation.
   build_hh_ss                  It builds the Hamiltonian and Overlap matrix from the sisl.dh class.
   make_contour                 A more sophisticated contour generator.
   make_kset                    Simple k-grid generator to sample the Brillouin zone.
   hsk                          Speed up Hk and Sk generation.
   process_ref_directions       Preprocess the reference directions input for the Builder object.
"""

from .constants import *
from .cpu_solvers import *
from .gpu_solvers import *
from .utilities import *
