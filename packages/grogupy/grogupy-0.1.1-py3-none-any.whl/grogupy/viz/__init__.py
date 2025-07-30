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
Visualization
=============

.. currentmodule:: grogupy.viz


This subpackage contains various routines to plot the system of magnetic entities
and pairs. Furthermore it will be able to plot the calculated magnetic exchange
parameters.

Functions
---------

.. autosummary::
   :toctree: _generated/

    plot_contour              Plots the contour for the integration.
    plot_kspace               Plots the Brillouin-zone sampling.
    plot_magnetic_entities    Plots the magnetic entities in the lattice.
    plot_pairs                Plots the pairs, with or without connections.
    plot_DMI                  Plots the DMI vectors.
    plot_DM_distance          Plots the magnitude of DM vectors as a function of distance.
    plot_Jiso_distance        Plots the isotropic exchange as a function of distance.
    plot_1D_convergence       Reads output files and create a plot for the convergence test.

Background information
----------------------

Currently all the functions are using the plotly library.
This decision was made because it can be used in the Jupyter
environment and supports interactive and 3D plots.

Examples
--------

For examples, see the *Visualize the exchange* in  :ref:`tutorials <quickstart-guide>`.

"""

from grogupy import __all__
from grogupy.config import CONFIG
from grogupy.physics import Builder, Contour, Kspace

from .plotters import *

__all__.extend(["plot_1D_convergence"])

CONFIG._Config__viz_loaded = True

setattr(Contour, "plot", plot_contour)
setattr(Kspace, "plot", plot_kspace)
setattr(Builder, "plot_DMI", plot_DMI)
setattr(Builder, "plot_magnetic_entities", plot_magnetic_entities)
setattr(Builder, "plot_pairs", plot_pairs)
setattr(Builder, "plot_DM_distance", plot_DM_distance)
setattr(Builder, "plot_Jiso_distance", plot_Jiso_distance)
