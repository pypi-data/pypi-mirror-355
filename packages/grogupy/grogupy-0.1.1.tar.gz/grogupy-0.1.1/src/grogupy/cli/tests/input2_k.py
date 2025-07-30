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

infolder = "./benchmarks/CrI3"
infile = "CrI3.fdf"


###############################################################################
#                            Convergence parameters
###############################################################################


# kset should be at leas 100x100 for 2D diatomic systems
kset = [3, 3, 1]
# eset should be 100 for insulators and 1000 for metals
eset = 10
# esetp should be 600 for insulators and 10000 for metals
esetp = 600
# emin None sets the minimum energy to the minimum energy in the eigfile
emin = None
# emax is at the Fermi level at 0
emax = 0
# the bottom of the energy contour should be shifted by -5 eV
emin_shift = -5
# the top of the energy contour can be shifted to the middle of the gap for
# insulators
emax_shift = 0


###############################################################################
#                                 Orientations
###############################################################################


# usually the DFT calculation axis is [0, 0, 1]
scf_xcf_orientation = [0, 0, 1]
# the reference directions for the energy derivations
ref_xcf_orientations = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


###############################################################################
#                      Magnetic entity and pair definitions
###############################################################################


# magnetic entities and pairs can be defined automatically from the cutoff
# radius and magnetic atoms
setup_from_range = False
magnetic_entities = [
    dict(atom=0),
    dict(atom=[0, 1]),
    dict(atom=0, l=2),
    dict(atom=0, orb=2),
    dict(orb=0),
]
pairs = [
    dict(ai=0, aj=1, Ruc=[0, 0, 0]),
    dict(ai=0, aj=1, Ruc=[1, 0, 0]),
    dict(ai=0, aj=0, Ruc=[1, 0, 0]),
]

###############################################################################
#                                Memory management
###############################################################################


# maximum number of pairs per loop, reduce it to avoid memory overflow
max_pairs_per_loop = 2
# in low memory mode we discard some temporary data that could be useful for
# interactive work
low_memory_mode = False
# sequential solver is better for large systems
greens_function_solver = "Sequential"
# maximum number of greens function samples per loop, when
# greens_function_solver is set to "Sequential", reduce it to avoid memory
# overflow on GPU for large systems
max_g_per_loop = 1000


###############################################################################
#                                 Solution methods
###############################################################################


# the spin model solvers solvers can be turned off, in this case only the
# energies upon rotations are meaningful
apply_spin_model = True
# the calculation of J and K from the energy derivations, either
# "generalised-fit", "generalised-grogu" or "isotropic-only"
spin_model = "generalised-grogu"
# parallelization should be turned on for efficiency
parallel_mode = "K"


###############################################################################
#                                   Output files
###############################################################################


# either total or local, which controls if only the magnetic
# entity's magnetic monent or the whole atom's magnetic moment is printed
# used by all output modes
out_magnetic_moment = "Total"

# save the magnopy file
save_magnopy = True
# precision of numerical values in the magnopy file
magnopy_precision = None
# add the simulation parameters to the magnopy file as comments
magnopy_comments = True

# save the Uppsala Atomistic Spin Dynamics software input files
# uses the outfolder and out_magentic_moment
save_UppASD = True
# add the simulation parameters to the cell.tmp.txt file as
# comments
uppasd_comments = True

# save the pickle file
save_pickle = True
"""
The compression level can be set to 0,1,2. Every other value defaults to 2.
0. This means that there is no compression at all.

1. This means, that the keys "_dh" and "_ds" are set
to None, because othervise the loading would be dependent
on the sisl version

2. This contains compression 1, but sets the keys "Gii",
"Gij", "Gji", "Vu1" and "Vu2" to [], to save space
"""
pickle_compress_level = 2

# output folder, for example the current folder
outfolder = "./src/grogupy/cli/tests/"
# outfile name
outfile = "test"


###############################################################################
###############################################################################
