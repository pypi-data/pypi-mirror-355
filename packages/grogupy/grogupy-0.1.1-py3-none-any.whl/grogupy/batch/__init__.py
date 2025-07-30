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
Batch calculations
==================

.. currentmodule:: grogupy.batch

This subpackage contains routines to automatically set up and run convergence 
tests and time the calculations.

Timers
------

One class to rule them all, one class to time them...

.. autosummary::
   :toctree: _generated/

   DefaultTimer                 This class measures and stores the runtime of each object.

Convergence
-----------

These are functions that can set up and execute different convergence tests or 
that can otherwise help with running in an HPC environment.

.. autosummary::
   :toctree: _generated/

Examples
--------

For examples, see the :ref:`tutorials <tutorials>`.

"""

from .converge import *
from .timing import *
