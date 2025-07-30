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

import argparse
import datetime
import os
from os.path import join
from timeit import default_timer as timer

import numpy as np

from grogupy import __citation__, __definitely_not_grogu__
from grogupy.config import CONFIG
from grogupy.io import (
    DEFAULT_INPUT,
    load_Builder,
    read_fdf,
    read_py,
    save,
    save_magnopy,
    save_UppASD,
    standardize_input,
)
from grogupy.physics import Builder, Contour, Hamiltonian, Kspace, PairList

# Only print on MPI root node
PRINTING = True
if CONFIG.is_CPU:
    if CONFIG.MPI_loaded:
        from mpi4py import MPI

        rank = MPI.COMM_WORLD.rank
        if rank != 0:
            PRINTING = False


def main():
    """Main entry point of the script."""

    # setup parser
    parser = argparse.ArgumentParser(
        description="This script takes a .py or a .fdf input files and runs grogupy with the given input."
    )
    parser.add_argument("file", nargs="?", help="Path to a .py or .fdfinput file.")
    parser.add_argument(
        "-c" "--cite",
        dest="cite",
        action="store_true",
        default=False,
        help="Print the citation of the package.",
    )
    # parameters from command line
    args = parser.parse_args()

    # print citation if needed
    if args.cite:
        print(__citation__ + __definitely_not_grogu__)
        if args.file is None:
            return

    # Reading input
    if args.file.endswith(".py"):
        params = read_py(args.file)
    elif args.file.endswith(".fdf"):
        params = read_fdf(args.file)
    else:
        raise Exception(f"Unknown input format: {args.file}!")

    params = standardize_input(params, defaults=DEFAULT_INPUT)

    if PRINTING:
        print("Simulation started at:", datetime.datetime.now())
    start = timer()

    # print input
    if PRINTING:
        print("\n\n\n")
        print(
            "################################################################################"
        )
        print("#                                   Inputs")
        print(
            "################################################################################"
        )
        for key, value in params.items():
            print(key, "\t\t\t", value)
        print(
            "################################################################################"
        )
        print(
            "################################################################################"
        )
        print("\n\n\n")

    # construct the input and output file paths
    infile = join(params["infolder"], params["infile"])
    if not infile.endswith(".fdf"):
        infile += ".fdf"
    outfile = join(params["outfolder"], params["outfile"])

    # Define simulation
    simulation = Builder(ref_xcf_orientations=params["refxcforientations"])

    # Add solvers and parallellizations
    simulation.low_memory_mode = params["lowmemorymode"]
    simulation.parallel_mode = params["parallelmode"]
    simulation.greens_function_solver = params["greensfunctionsolver"]
    simulation.max_g_per_loop = params["maxgperloop"]
    simulation.apply_spin_model = params["applyspinmodel"]
    simulation.spin_model = params["spinmodel"]

    # check for the appropriate output formats if only the energies are
    # evaluated
    if not params["applyspinmodel"]:
        if params["savemagnopy"]:
            raise Exception(
                "magnopy output is not available if only the energies are evaluated!"
            )
        if params["saveuppasd"]:
            raise Exception(
                "UppASD output is not available if only the energies are evaluated!"
            )
        if not params["savepickle"]:
            raise Exception(
                "Pickle output format is mandatory, because it contains the energies!"
            )

    # Define Kspace
    kspace = Kspace(
        kset=params["kset"],
    )

    # Define Contour
    contour = Contour(
        eset=params["eset"],
        esetp=params["esetp"],
        emin=params["emin"],
        emax=params["emax"],
        emin_shift=params["eminshift"],
        emax_shift=params["emaxshift"],
        eigfile=infile,
    )

    # Define Hamiltonian from sisl
    hamiltonian = Hamiltonian(
        infile=infile,
        scf_xcf_orientation=params["scfxcforientation"],
    )

    # Add instances to the simulation
    simulation.add_kspace(kspace)
    simulation.add_contour(contour)
    simulation.add_hamiltonian(hamiltonian)

    # Set up magnetic entities and pairs
    # If it is not set up from range:
    if not params["setupfromrange"]:
        simulation.add_magnetic_entities(params["magneticentities"])
        simulation.add_pairs(params["pairs"])

    # If it is automatically set up from range
    if params["setupfromrange"]:
        simulation.setup_from_range(
            params["radius"], params["atomicsubset"], **params["kwargsformagent"]
        )

    if PRINTING:
        print("setup:", (timer() - start) / 60, " min")
        print("\n\n\n")
        print(
            "################################################################################"
        )
        print(
            "################################################################################"
        )
        print(simulation)
        print(
            "################################################################################"
        )
        print(
            "################################################################################"
        )
        print("\n\n\n")

    if params["maxpairsperloop"] < len(simulation.pairs):
        number_of_chunks: int = (
            np.floor(len(simulation.pairs) / params["maxpairsperloop"]) + 1
        )
        pair_chunks = np.array_split(simulation.pairs.toarray(), number_of_chunks)

        if PRINTING:
            print("\n\n\n")
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print(
                "Maximum number of pairs per loop exceeded! To avoid memory overflow pairs are being separated."
            )
            print(f"Maximum number of pairs per loop {params['maxpairsperloop']}")
            print(
                f"pairs are being separated to {number_of_chunks} chunks, each chunk containing {[len(c) for c in pair_chunks]} pairs."
            )
            print("These will be ran as separate and they will be concatenated.")
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print("\n\n\n")

        # run chunks
        for i, chunk in enumerate(pair_chunks):
            simulation.pairs = PairList(chunk)
            simulation.solve(print_memory=True)
            if PRINTING:
                save(
                    object=simulation,
                    path=outfile + "_temp_" + str(i) + ".pkl",
                    compress=params["picklecompresslevel"],
                )
        if PRINTING:
            # add pairs to Builder
            new_pairs: PairList = PairList()
            for i in range(len(pair_chunks)):
                new_pairs += load_Builder(outfile + "_temp_" + str(i) + ".pkl").pairs
            simulation.pairs = new_pairs
            # remove hamiltonian from magnetic entities so the comparison does not fail
            if params["picklecompresslevel"] != 0:
                for mag_ent in simulation.magnetic_entities:
                    mag_ent._dh = None
                    mag_ent._ds = None
            if params["picklecompresslevel"] >= 2:
                for mag_ent in simulation.magnetic_entities:
                    mag_ent._Gii = []
                    mag_ent._Vu1 = []
                    mag_ent._Vu2 = []
    else:
        # Solve
        simulation.solve(print_memory=True)

    if PRINTING:
        print("\n\n\n")
        print(
            "################################################################################"
        )
        print(
            "################################################################################"
        )
        print("solved:", (timer() - start) / 60, "min")
        print(simulation.times.times)
        if not params["applyspinmodel"]:
            print("THE ENERGIES ARE CALCULATED, BUT THE SUMMARY IS NOT AVAILABLE!")
            print("THE ENERGIES ARE CALCULATED, BUT THE SUMMARY IS NOT AVAILABLE!")
            print("THE ENERGIES ARE CALCULATED, BUT THE SUMMARY IS NOT AVAILABLE!")
        else:
            print(simulation.to_magnopy())
        print(
            "################################################################################"
        )
        print(
            "################################################################################"
        )
        print("\n\n\n")

        if params["savepickle"]:
            save(
                object=simulation, path=outfile, compress=params["picklecompresslevel"]
            )
            print("Saved pickle")

        if params["savemagnopy"]:
            save_magnopy(
                simulation,
                path=outfile,
                magnetic_moment=params["outmagneticmoment"],
                precision=params["magnopyprecision"],
                comments=params["magnopycomments"],
            )
            print("Saved magnopy")

        if params["saveuppasd"]:
            # create folder if it does not exist
            UppASD_folder = outfile + "_UppASD_output"
            if not os.path.isdir(UppASD_folder):
                os.mkdir(UppASD_folder)
            # save
            save_UppASD(
                simulation,
                folder=UppASD_folder,
                fast_compare=True,
                magnetic_moment=params["outmagneticmoment"],
                comments=params["uppasdcomments"],
            )
            print("Saved UppASD")

    if PRINTING:
        if params["maxpairsperloop"] < len(simulation.pairs):
            for i in range(len(pair_chunks)):
                os.remove(outfile + "_temp_" + str(i) + ".pkl")

        print("\n\n\n")
        print(__definitely_not_grogu__)
        print("Simulation ended at:", datetime.datetime.now())


if __name__ == "__main__":
    main()
