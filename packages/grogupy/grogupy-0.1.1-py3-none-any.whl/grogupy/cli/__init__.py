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
Command line interface for grogupy
==================================

This module does not contain functions, but provides a command line
interface for grogupy. It loads the input parameters from a Python
file and runs the simulation or makes analysis.

Scripts
-------

.. autosummary::
   :toctree: _generated/

    run                     Takes an input file and runs a simulation from it.
    analyze                 Takes a .pkl output file and creates an .html file from it with useful plots.
    check_convergence       Load results from multiple .pkl files and do convergence analysis with them.

Examples
--------

For examples, see the `running in HPC <running_in_hpc>`_ section in the documentation.

"""

from grogupy import CONFIG

from .run import *

if CONFIG.viz_loaded:
    from .analyze import *
    from .check_convergence import *
