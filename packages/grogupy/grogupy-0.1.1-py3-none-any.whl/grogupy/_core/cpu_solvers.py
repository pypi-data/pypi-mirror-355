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

from typing import TYPE_CHECKING

from numpy.typing import NDArray

if TYPE_CHECKING:
    from grogupy.physics.builder import Builder

import numpy as np

from grogupy._tqdm import _tqdm
from grogupy.config import CONFIG
from grogupy.physics.utilities import interaction_energy

from .utilities import calc_Vu, onsite_projection, tau_u

if CONFIG.MPI_loaded:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    parallel_size = CONFIG.parallel_size
    root_node = 0
    rank = comm.Get_rank()

    def default_solver(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method without MPI parallelization.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is not parallized
        at all. It uses the `greens_function_solver` instance variable which
        controls the solution method over the energy samples. This is the
        slowest method, but it does not have extra depedencies.

        Parameters
        ----------
        builder: Builder
            The main grogupy object
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        # this is not parallel
        if rank == root_node:
            # checks for setup
            if builder.kspace is None:
                raise Exception("Kspace is not defined!")
            if builder.contour is None:
                raise Exception("Kspace is not defined!")
            if builder.hamiltonian is None:
                raise Exception("Kspace is not defined!")

            # reset hamiltonians, magnetic entities and pairs
            builder._rotated_hamiltonians = []
            for mag_ent in builder.magnetic_entities:
                mag_ent.reset()
            for pair in builder.pairs:
                pair.reset()

            # calculate and print memory stuff
            # 16 is the size of complex numbers in byte, when using np.float64
            H_mem = np.sum(
                [
                    np.prod(builder.hamiltonian.H.shape) * 16,
                    np.prod(builder.hamiltonian.S.shape) * 16,
                ]
            )
            mag_ent_mem = (
                builder.contour.eset * builder.magnetic_entities.SBS**2
            ).sum() * 16
            pair_mem = (
                builder.contour.eset * builder.pairs.SBS1 * builder.pairs.SBS2
            ).sum() * 16
            if print_memory:
                print("\n\n\n")
                print(
                    "################################################################################"
                )
                print(
                    "################################################################################"
                )
                print("Memory allocated on each MPI rank:")
                print(f"Memory allocated by rotated Hamilonian: {H_mem/1e6} MB")
                print(f"Memory allocated by magnetic entities: {mag_ent_mem/1e6} MB")
                print(f"Memory allocated by pairs: {pair_mem/1e6} MB")
                print(
                    f"Total memory allocated in RAM: {(H_mem+mag_ent_mem+pair_mem)/1e6} MB"
                )
                print(
                    "--------------------------------------------------------------------------------"
                )
                if builder.greens_function_solver[0].lower() == "p":  # parallel solver
                    G_mem = (
                        builder.contour.eset * np.prod(builder.hamiltonian.H.shape) * 16
                    )
                elif (
                    builder.greens_function_solver[0].lower() == "s"
                ):  # sequentia solver
                    G_mem = (
                        builder.max_g_per_loop
                        * np.prod(builder.hamiltonian.H.shape)
                        * 16
                    )
                else:
                    raise Exception("Unknown Greens function solver!")

                print(f"Memory allocated for Greens function samples: {G_mem/1e6} MB")
                print(
                    f"Total peak memory during solution: {(H_mem+mag_ent_mem+pair_mem+G_mem*25)/1e6} MB"
                )
                print(
                    "################################################################################"
                )
                print(
                    "################################################################################"
                )
                print("\n\n\n")

            # iterate over the reference directions (quantization axes)
            for i, orient in enumerate(builder.ref_xcf_orientations):
                # obtain rotated Hamiltonian
                if builder.low_memory_mode:
                    rot_H = builder.hamiltonian
                else:
                    rot_H = builder.hamiltonian.copy()
                if not np.allclose(rot_H.orientation, orient["o"]):
                    rot_H.rotate(orient["o"])

                # setup empty Greens function holders for integration and
                # initialize rotation storage
                for mag_ent in builder.magnetic_entities:
                    mag_ent._Vu1_tmp = []
                    mag_ent._Vu2_tmp = []
                    mag_ent._Gii_tmp = np.zeros(
                        (builder.contour.eset, mag_ent.SBS, mag_ent.SBS),
                        dtype="complex128",
                    )
                for pair in builder.pairs:
                    pair._Gij_tmp = np.zeros(
                        (builder.contour.eset, pair.SBS1, pair.SBS2), dtype="complex128"
                    )
                    pair._Gji_tmp = np.zeros(
                        (builder.contour.eset, pair.SBS2, pair.SBS1), dtype="complex128"
                    )

                # sampling the integrand on the contour and the BZ
                kpoints = _tqdm(builder.kspace.kpoints, desc=f"Rotation {i+1}")
                for j, k in enumerate(kpoints):

                    # weight of k point in BZ integral
                    wk: float = builder.kspace.weights[j]

                    # calculate Hamiltonian and Overlap matrix in a given k point
                    Hk, Sk = rot_H.HkSk(k)

                    # Calculates the Greens function on all the energy levels
                    if (
                        builder.greens_function_solver[0].lower() == "p"
                    ):  # parallel solver
                        Gk = np.linalg.inv(
                            Sk
                            * builder.contour.samples.reshape(
                                builder.contour.eset, 1, 1
                            )
                            - Hk
                        )

                        # store the Greens function slice of the magnetic entities
                        for mag_ent in builder.magnetic_entities:
                            mag_ent._Gii_tmp += (
                                onsite_projection(
                                    Gk,
                                    mag_ent._spin_box_indices,
                                    mag_ent._spin_box_indices,
                                )
                                * wk
                            )

                        for pair in builder.pairs:
                            # add phase shift based on the cell difference
                            phase: NDArray = np.exp(
                                1j * 2 * np.pi * k @ pair.supercell_shift.T
                            )
                            # store the Greens function slice of the pairs
                            pair._Gij_tmp += (
                                onsite_projection(Gk, pair.SBI1, pair.SBI2) * phase * wk
                            )
                            pair._Gji_tmp += (
                                onsite_projection(Gk, pair.SBI2, pair.SBI1) / phase * wk
                            )

                    # solve Greens function sequentially for the energies, because of memory bound
                    elif (
                        builder.greens_function_solver[0].lower() == "s"
                    ):  # sequential solver

                        # make chunks for reduced parallelization over energy sample points
                        number_of_chunks = (
                            np.floor(builder.contour.eset / builder.max_g_per_loop) + 1
                        )
                        # constrain to sensible size
                        if number_of_chunks > builder.contour.eset:
                            number_of_chunks = builder.contour.eset

                        # create batches using slices on every instance
                        slices = np.array_split(
                            range(builder.contour.eset), number_of_chunks
                        )
                        # fills the holders sequentially by the Greens function slices on
                        # a given energy
                        for slice in slices:
                            Gk = np.linalg.inv(
                                Sk
                                * builder.contour.samples[slice].reshape(
                                    len(slice), 1, 1
                                )
                                - Hk
                            )

                            # store the Greens function slice of the magnetic entities
                            for mag_ent in builder.magnetic_entities:
                                mag_ent._Gii_tmp[slice] += (
                                    onsite_projection(
                                        Gk,
                                        mag_ent._spin_box_indices,
                                        mag_ent._spin_box_indices,
                                    )
                                    * wk
                                )

                            for pair in builder.pairs:
                                # add phase shift based on the cell difference
                                phase: NDArray = np.exp(
                                    1j * 2 * np.pi * k @ pair.supercell_shift.T
                                )
                                # store the Greens function slice of the pairs
                                pair._Gij_tmp[slice] += (
                                    onsite_projection(Gk, pair.SBI1, pair.SBI2)
                                    * phase
                                    * wk
                                )
                                pair._Gji_tmp[slice] += (
                                    onsite_projection(Gk, pair.SBI2, pair.SBI1)
                                    / phase
                                    * wk
                                )
                    else:
                        raise Exception("Unknown Green's function solver!")

                # these are the rotations perpendicular to the quantization axis
                for u in orient["vw"]:
                    # section 2.H
                    H_XCF = rot_H.extract_exchange_field()[3]
                    Tu: NDArray = np.kron(
                        np.eye(int(builder.hamiltonian.NO / 2), dtype=int), tau_u(u)
                    )
                    Vu1, Vu2 = calc_Vu(H_XCF[rot_H.uc_in_sc_index], Tu)

                    for mag_ent in _tqdm(
                        builder.magnetic_entities,
                        desc="Setup perturbations for rotated hamiltonian",
                    ):
                        # fill up the perturbed potentials (for now) based on the on-site projections
                        mag_ent._Vu1_tmp.append(
                            onsite_projection(
                                Vu1,
                                mag_ent._spin_box_indices,
                                mag_ent._spin_box_indices,
                            )
                        )
                        mag_ent._Vu2_tmp.append(
                            onsite_projection(
                                Vu2,
                                mag_ent._spin_box_indices,
                                mag_ent._spin_box_indices,
                            )
                        )

                if builder.spin_model == "isotropic-only":
                    for pair in builder.pairs:
                        pair.energies = np.array(
                            [
                                [
                                    interaction_energy(
                                        pair.M1._Vu1_tmp,
                                        pair.M2._Vu1_tmp,
                                        pair._Gij_tmp,
                                        pair._Gji_tmp,
                                        builder.contour.weights,
                                    )
                                ]
                            ]
                        )
                else:
                    # calculate energies in the current reference hamiltonian direction
                    for mag_ent in builder.magnetic_entities:
                        mag_ent.calculate_energies(
                            builder.contour.weights,
                            append=True,
                            third_direction=builder.spin_model == "generalised-grogu",
                        )
                    for pair in builder.pairs:
                        pair.calculate_energies(builder.contour.weights, append=True)

                # if we want to keep all the information for some reason we can do it
                if not builder.low_memory_mode:
                    builder._rotated_hamiltonians.append(rot_H)
                    for mag_ent in builder.magnetic_entities:
                        mag_ent._Vu1.append(mag_ent._Vu1_tmp)
                        mag_ent._Vu2.append(mag_ent._Vu2_tmp)
                        mag_ent._Gii.append(mag_ent._Gii_tmp)
                    for pair in builder.pairs:
                        pair._Gij.append(pair._Gij_tmp)
                        pair._Gji.append(pair._Gji_tmp)
                # or fill with empty stuff
                else:
                    for mag_ent in builder.magnetic_entities:
                        mag_ent._Vu1.append([])
                        mag_ent._Vu2.append([])
                        mag_ent._Gii.append([])
                    for pair in builder.pairs:
                        pair._Gij.append([])
                        pair._Gji.append([])

                    # rotate back hamiltonian for the original DFT orientation
                    rot_H.rotate(rot_H.scf_xcf_orientation)

            # finalize energies of the magnetic entities and pairs
            # calculate magnetic parameters
            for mag_ent in builder.magnetic_entities:
                # delete temporary stuff
                del mag_ent._Gii_tmp
                del mag_ent._Vu1_tmp
                del mag_ent._Vu2_tmp

                if builder.apply_spin_model:
                    if builder.spin_model == "generalised-fit":
                        mag_ent.fit_anisotropy_tensor(builder.ref_xcf_orientations)
                    elif builder.spin_model == "generalised-grogu":
                        mag_ent.calculate_anisotropy()
                    else:
                        pass

            for pair in builder.pairs:
                # delete temporary stuff
                del pair._Gij_tmp
                del pair._Gji_tmp

                if builder.apply_spin_model:
                    if builder.spin_model == "generalised-fit":
                        pair.fit_exchange_tensor(builder.ref_xcf_orientations)
                    elif builder.spin_model == "generalised-grogu":
                        pair.calculate_exchange_tensor()
                    elif builder.spin_model == "isotropic-only":
                        pair.calculate_isotropic_only()
                    else:
                        raise Exception(
                            f"Unknown spin model: {builder.spin_model}! Use apply_spin_model=False"
                        )

    def solve_parallel_over_k(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is parallelized over
        k-points. It uses the `greens_function_solver` instance variable which
        controls the solution method over the energy samples. Generally this is
        the fastest solution method for smaller systems.

        Parameters
        ----------
        builder: Builder
            The main grogupy object
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        # wait for pre process to finish before start
        comm.Barrier()

        # checks for setup
        if builder.kspace is None:
            raise Exception("Kspace is not defined!")
        if builder.contour is None:
            raise Exception("Kspace is not defined!")
        if builder.hamiltonian is None:
            raise Exception("Kspace is not defined!")

        # reset hamiltonians, magnetic entities and pairs
        builder._rotated_hamiltonians = []
        for mag_ent in builder.magnetic_entities:
            mag_ent.reset()
        for pair in builder.pairs:
            pair.reset()

        # calculate and print memory stuff
        # 16 is the size of complex numbers in byte, when using np.float64
        H_mem = np.sum(
            [
                np.prod(builder.hamiltonian.H.shape) * 16,
                np.prod(builder.hamiltonian.S.shape) * 16,
            ]
        )
        mag_ent_mem = (
            builder.contour.eset * builder.magnetic_entities.SBS**2
        ).sum() * 16
        pair_mem = (
            builder.contour.eset * builder.pairs.SBS1 * builder.pairs.SBS2
        ).sum() * 16
        if print_memory and rank == root_node:
            print("\n\n\n")
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print("Memory allocated on each MPI rank:")
            print(f"Memory allocated by rotated Hamilonian: {H_mem/1e6} MB")
            print(f"Memory allocated by magnetic entities: {mag_ent_mem/1e6} MB")
            print(f"Memory allocated by pairs: {pair_mem/1e6} MB")
            print(
                f"Total memory allocated in RAM: {(H_mem+mag_ent_mem+pair_mem)/1e6} MB"
            )
            print(
                "--------------------------------------------------------------------------------"
            )
            if builder.greens_function_solver[0].lower() == "p":  # parallel solver
                G_mem = builder.contour.eset * np.prod(builder.hamiltonian.H.shape) * 16
            elif builder.greens_function_solver[0].lower() == "s":  # sequentia solver
                G_mem = (
                    builder.max_g_per_loop * np.prod(builder.hamiltonian.H.shape) * 16
                )
            else:
                raise Exception("Unknown Greens function solver!")

            print(f"Memory allocated for Greens function samples: {G_mem/1e6} MB")
            print(
                f"Total peak memory during solution: {(H_mem+mag_ent_mem+pair_mem+G_mem*25)/1e6} MB"
            )
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print("\n\n\n")

        # iterate over the reference directions (quantization axes)
        for i, orient in enumerate(builder.ref_xcf_orientations):
            # obtain rotated Hamiltonian
            if builder.low_memory_mode:
                rot_H = builder.hamiltonian
            else:
                rot_H = builder.hamiltonian.copy()
            if not np.allclose(rot_H.orientation, orient["o"]):
                rot_H.rotate(orient["o"])

            # setup empty Greens function holders for integration and
            # initialize rotation storage
            for mag_ent in builder.magnetic_entities:
                mag_ent._Vu1_tmp = []
                mag_ent._Vu2_tmp = []
                mag_ent._Gii_tmp = np.zeros(
                    (builder.contour.eset, mag_ent.SBS, mag_ent.SBS),
                    dtype="complex128",
                )
            for pair in builder.pairs:
                pair._Gij_tmp = np.zeros(
                    (builder.contour.eset, pair.SBS1, pair.SBS2), dtype="complex128"
                )
                pair._Gji_tmp = np.zeros(
                    (builder.contour.eset, pair.SBS2, pair.SBS1), dtype="complex128"
                )

            # split k points to parallelize
            # (this could be outside loop, but it was an easy fix for the
            # reset of tqdm in each reference direction)
            parallel_k: list = np.array_split(builder.kspace.kpoints, parallel_size)
            parallel_w: list = np.array_split(builder.kspace.weights, parallel_size)

            if rank == root_node:
                parallel_k[rank] = _tqdm(
                    parallel_k[rank],
                    desc=f"Rotation {i+1}, parallel over k on CPU{rank}",
                )
            for j, k in enumerate(parallel_k[rank]):

                # weight of k point in BZ integral
                wk: float = parallel_w[rank][j]

                # calculate Hamiltonian and Overlap matrix in a given k point
                Hk, Sk = rot_H.HkSk(k)

                # Calculates the Greens function on all the energy levels
                if builder.greens_function_solver[0].lower() == "p":  # parallel solver
                    Gk = np.linalg.inv(
                        Sk * builder.contour.samples.reshape(builder.contour.eset, 1, 1)
                        - Hk
                    )

                    # store the Greens function slice of the magnetic entities
                    for mag_ent in builder.magnetic_entities:
                        mag_ent._Gii_tmp += (
                            onsite_projection(
                                Gk, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                            )
                            * wk
                        )

                    for pair in builder.pairs:
                        # add phase shift based on the cell difference
                        phase: NDArray = np.exp(
                            1j * 2 * np.pi * k @ pair.supercell_shift.T
                        )
                        # store the Greens function slice of the pairs
                        pair._Gij_tmp += (
                            onsite_projection(Gk, pair.SBI1, pair.SBI2) * phase * wk
                        )
                        pair._Gji_tmp += (
                            onsite_projection(Gk, pair.SBI2, pair.SBI1) / phase * wk
                        )

                # solve Greens function sequentially for the energies, because of memory bound
                elif (
                    builder.greens_function_solver[0].lower() == "s"
                ):  # sequential solver

                    # make chunks for reduced parallelization over energy sample points
                    number_of_chunks = (
                        np.floor(builder.contour.eset / builder.max_g_per_loop) + 1
                    )
                    # constrain to sensible size
                    if number_of_chunks > builder.contour.eset:
                        number_of_chunks = builder.contour.eset

                    # create batches using slices on every instance
                    slices = np.array_split(
                        range(builder.contour.eset), number_of_chunks
                    )
                    # fills the holders sequentially by the Greens function slices on
                    # a given energy
                    for slice in slices:
                        Gk = np.linalg.inv(
                            Sk
                            * builder.contour.samples[slice].reshape(len(slice), 1, 1)
                            - Hk
                        )

                        # store the Greens function slice of the magnetic entities
                        for mag_ent in builder.magnetic_entities:
                            mag_ent._Gii_tmp[slice] += (
                                onsite_projection(
                                    Gk,
                                    mag_ent._spin_box_indices,
                                    mag_ent._spin_box_indices,
                                )
                                * wk
                            )

                        for pair in builder.pairs:
                            # add phase shift based on the cell difference
                            phase: NDArray = np.exp(
                                1j * 2 * np.pi * k @ pair.supercell_shift.T
                            )
                            # store the Greens function slice of the pairs
                            pair._Gij_tmp[slice] += (
                                onsite_projection(Gk, pair.SBI1, pair.SBI2) * phase * wk
                            )
                            pair._Gji_tmp[slice] += (
                                onsite_projection(Gk, pair.SBI2, pair.SBI1) / phase * wk
                            )
                else:
                    raise Exception("Unknown Green's function solver!")

            # sum reduce partial results of mpi nodes and delete temprorary stuff
            for mag_ent in builder.magnetic_entities:
                mag_ent._Gii_reduce = np.zeros(
                    (builder.contour.eset, mag_ent.SBS, mag_ent.SBS),
                    dtype="complex128",
                )
                comm.Reduce(mag_ent._Gii_tmp, mag_ent._Gii_reduce, root=root_node)
                mag_ent._Gii_tmp = mag_ent._Gii_reduce
                del mag_ent._Gii_reduce

            for pair in builder.pairs:
                pair._Gij_reduce = np.zeros(
                    (builder.contour.eset, pair.SBS1, pair.SBS2), dtype="complex128"
                )
                pair._Gji_reduce = np.zeros(
                    (builder.contour.eset, pair.SBS2, pair.SBS1), dtype="complex128"
                )
                comm.Reduce(pair._Gij_tmp, pair._Gij_reduce, root=root_node)
                comm.Reduce(pair._Gji_tmp, pair._Gji_reduce, root=root_node)
                pair._Gij_tmp = pair._Gij_reduce
                pair._Gji_tmp = pair._Gji_reduce
                del pair._Gij_reduce
                del pair._Gji_reduce

            # these are the rotations perpendicular to the quantization axis
            for u in orient["vw"]:
                # section 2.H
                H_XCF = rot_H.extract_exchange_field()[3]
                Tu: NDArray = np.kron(
                    np.eye(int(builder.hamiltonian.NO / 2), dtype=int), tau_u(u)
                )
                Vu1, Vu2 = calc_Vu(H_XCF[rot_H.uc_in_sc_index], Tu)

                for mag_ent in _tqdm(
                    builder.magnetic_entities,
                    desc="Setup perturbations for rotated hamiltonian",
                ):
                    # fill up the perturbed potentials (for now) based on the on-site projections
                    mag_ent._Vu1_tmp.append(
                        onsite_projection(
                            Vu1, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                        )
                    )
                    mag_ent._Vu2_tmp.append(
                        onsite_projection(
                            Vu2, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                        )
                    )

            if builder.spin_model == "isotropic-only":
                for pair in builder.pairs:
                    pair.energies = np.array(
                        [
                            [
                                interaction_energy(
                                    pair.M1._Vu1_tmp,
                                    pair.M2._Vu1_tmp,
                                    pair._Gij_tmp,
                                    pair._Gji_tmp,
                                    builder.contour.weights,
                                )
                            ]
                        ]
                    )
            else:
                # calculate energies in the current reference hamiltonian direction
                for mag_ent in builder.magnetic_entities:
                    mag_ent.calculate_energies(
                        builder.contour.weights,
                        append=True,
                        third_direction=builder.spin_model == "generalised-grogu",
                    )
                for pair in builder.pairs:
                    pair.calculate_energies(builder.contour.weights, append=True)

            # if we want to keep all the information for some reason we can do it
            if not builder.low_memory_mode:
                builder._rotated_hamiltonians.append(rot_H)
                for mag_ent in builder.magnetic_entities:
                    mag_ent._Vu1.append(mag_ent._Vu1_tmp)
                    mag_ent._Vu2.append(mag_ent._Vu2_tmp)
                    mag_ent._Gii.append(mag_ent._Gii_tmp)
                for pair in builder.pairs:
                    pair._Gij.append(pair._Gij_tmp)
                    pair._Gji.append(pair._Gji_tmp)
            # or fill with empty stuff
            else:
                for mag_ent in builder.magnetic_entities:
                    mag_ent._Vu1.append([])
                    mag_ent._Vu2.append([])
                    mag_ent._Gii.append([])
                for pair in builder.pairs:
                    pair._Gij.append([])
                    pair._Gji.append([])

                # rotate back hamiltonian for the original DFT orientation
                rot_H.rotate(rot_H.scf_xcf_orientation)

        # wait for everyone in the end of loop
        comm.Barrier()

        # finalize energies of the magnetic entities and pairs
        # calculate magnetic parameters
        for mag_ent in builder.magnetic_entities:
            # delete temporary stuff
            del mag_ent._Gii_tmp
            del mag_ent._Vu1_tmp
            del mag_ent._Vu2_tmp

            if builder.apply_spin_model:
                if builder.spin_model == "generalised-fit":
                    mag_ent.fit_anisotropy_tensor(builder.ref_xcf_orientations)
                elif builder.spin_model == "generalised-grogu":
                    mag_ent.calculate_anisotropy()
                else:
                    pass

        for pair in builder.pairs:
            # delete temporary stuff
            del pair._Gij_tmp
            del pair._Gji_tmp

            if builder.apply_spin_model:
                if builder.spin_model == "generalised-fit":
                    pair.fit_exchange_tensor(builder.ref_xcf_orientations)
                elif builder.spin_model == "generalised-grogu":
                    pair.calculate_exchange_tensor()
                elif builder.spin_model == "isotropic-only":
                    pair.calculate_isotropic_only()
                else:
                    raise Exception(
                        f"Unknown spin model: {builder.spin_model}! Use apply_spin_model=False"
                    )

else:

    def default_solver(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method without MPI parallelization.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is not parallized
        at all. It uses the `greens_function_solver` instance variable which
        controls the solution method over the energy samples. This is the
        slowest method, but it does not have extra depedencies.

        Parameters
        ----------
        builder: Builder
            The main grogupy object
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        # checks for setup
        if builder.kspace is None:
            raise Exception("Kspace is not defined!")
        if builder.contour is None:
            raise Exception("Kspace is not defined!")
        if builder.hamiltonian is None:
            raise Exception("Kspace is not defined!")

        # reset hamiltonians, magnetic entities and pairs
        builder._rotated_hamiltonians = []
        for mag_ent in builder.magnetic_entities:
            mag_ent.reset()
        for pair in builder.pairs:
            pair.reset()

        # calculate and print memory stuff
        # 16 is the size of complex numbers in byte, when using np.float64
        H_mem = np.sum(
            [
                np.prod(builder.hamiltonian.H.shape) * 16,
                np.prod(builder.hamiltonian.S.shape) * 16,
            ]
        )
        mag_ent_mem = (
            builder.contour.eset * builder.magnetic_entities.SBS**2
        ).sum() * 16
        pair_mem = (
            builder.contour.eset * builder.pairs.SBS1 * builder.pairs.SBS2
        ).sum() * 16
        if print_memory:
            print("\n\n\n")
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print("Memory allocated on each MPI rank:")
            print(f"Memory allocated by rotated Hamilonian: {H_mem/1e6} MB")
            print(f"Memory allocated by magnetic entities: {mag_ent_mem/1e6} MB")
            print(f"Memory allocated by pairs: {pair_mem/1e6} MB")
            print(
                f"Total memory allocated in RAM: {(H_mem+mag_ent_mem+pair_mem)/1e6} MB"
            )
            print(
                "--------------------------------------------------------------------------------"
            )
            if builder.greens_function_solver[0].lower() == "p":  # parallel solver
                G_mem = builder.contour.eset * np.prod(builder.hamiltonian.H.shape) * 16
            elif builder.greens_function_solver[0].lower() == "s":  # sequentia solver
                G_mem = (
                    builder.max_g_per_loop * np.prod(builder.hamiltonian.H.shape) * 16
                )
            else:
                raise Exception("Unknown Greens function solver!")

            print(f"Memory allocated for Greens function samples: {G_mem/1e6} MB")
            print(
                f"Total peak memory during solution: {(H_mem+mag_ent_mem+pair_mem+G_mem*25)/1e6} MB"
            )
            print(
                "################################################################################"
            )
            print(
                "################################################################################"
            )
            print("\n\n\n")

        # iterate over the reference directions (quantization axes)
        for i, orient in enumerate(builder.ref_xcf_orientations):
            # obtain rotated Hamiltonian
            if builder.low_memory_mode:
                rot_H = builder.hamiltonian
            else:
                rot_H = builder.hamiltonian.copy()
            if not np.allclose(rot_H.orientation, orient["o"]):
                rot_H.rotate(orient["o"])

            # setup empty Greens function holders for integration and
            # initialize rotation storage
            for mag_ent in builder.magnetic_entities:
                mag_ent._Vu1_tmp = []
                mag_ent._Vu2_tmp = []
                mag_ent._Gii_tmp = np.zeros(
                    (builder.contour.eset, mag_ent.SBS, mag_ent.SBS),
                    dtype="complex128",
                )
            for pair in builder.pairs:
                pair._Gij_tmp = np.zeros(
                    (builder.contour.eset, pair.SBS1, pair.SBS2), dtype="complex128"
                )
                pair._Gji_tmp = np.zeros(
                    (builder.contour.eset, pair.SBS2, pair.SBS1), dtype="complex128"
                )

            # sampling the integrand on the contour and the BZ
            kpoints = _tqdm(builder.kspace.kpoints, desc=f"Rotation {i+1}")
            for j, k in enumerate(kpoints):

                # weight of k point in BZ integral
                wk: float = builder.kspace.weights[j]

                # calculate Hamiltonian and Overlap matrix in a given k point
                Hk, Sk = rot_H.HkSk(k)

                # Calculates the Greens function on all the energy levels
                if builder.greens_function_solver[0].lower() == "p":  # parallel solver
                    Gk = np.linalg.inv(
                        Sk * builder.contour.samples.reshape(builder.contour.eset, 1, 1)
                        - Hk
                    )

                    # store the Greens function slice of the magnetic entities
                    for mag_ent in builder.magnetic_entities:
                        mag_ent._Gii_tmp += (
                            onsite_projection(
                                Gk, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                            )
                            * wk
                        )

                    for pair in builder.pairs:
                        # add phase shift based on the cell difference
                        phase: NDArray = np.exp(
                            1j * 2 * np.pi * k @ pair.supercell_shift.T
                        )
                        # store the Greens function slice of the pairs
                        pair._Gij_tmp += (
                            onsite_projection(Gk, pair.SBI1, pair.SBI2) * phase * wk
                        )
                        pair._Gji_tmp += (
                            onsite_projection(Gk, pair.SBI2, pair.SBI1) / phase * wk
                        )

                # solve Greens function sequentially for the energies, because of memory bound
                elif (
                    builder.greens_function_solver[0].lower() == "s"
                ):  # sequential solver

                    # make chunks for reduced parallelization over energy sample points
                    number_of_chunks = (
                        np.floor(builder.contour.eset / builder.max_g_per_loop) + 1
                    )
                    # constrain to sensible size
                    if number_of_chunks > builder.contour.eset:
                        number_of_chunks = builder.contour.eset

                    # create batches using slices on every instance
                    slices = np.array_split(
                        range(builder.contour.eset), number_of_chunks
                    )
                    # fills the holders sequentially by the Greens function slices on
                    # a given energy
                    for slice in slices:
                        Gk = np.linalg.inv(
                            Sk
                            * builder.contour.samples[slice].reshape(len(slice), 1, 1)
                            - Hk
                        )

                        # store the Greens function slice of the magnetic entities
                        for mag_ent in builder.magnetic_entities:
                            mag_ent._Gii_tmp[slice] += (
                                onsite_projection(
                                    Gk,
                                    mag_ent._spin_box_indices,
                                    mag_ent._spin_box_indices,
                                )
                                * wk
                            )

                        for pair in builder.pairs:
                            # add phase shift based on the cell difference
                            phase: NDArray = np.exp(
                                1j * 2 * np.pi * k @ pair.supercell_shift.T
                            )
                            # store the Greens function slice of the pairs
                            pair._Gij_tmp[slice] += (
                                onsite_projection(Gk, pair.SBI1, pair.SBI2) * phase * wk
                            )
                            pair._Gji_tmp[slice] += (
                                onsite_projection(Gk, pair.SBI2, pair.SBI1) / phase * wk
                            )
                else:
                    raise Exception("Unknown Green's function solver!")

            # these are the rotations perpendicular to the quantization axis
            for u in orient["vw"]:
                # section 2.H
                H_XCF = rot_H.extract_exchange_field()[3]
                Tu: NDArray = np.kron(
                    np.eye(int(builder.hamiltonian.NO / 2), dtype=int), tau_u(u)
                )
                Vu1, Vu2 = calc_Vu(H_XCF[rot_H.uc_in_sc_index], Tu)

                for mag_ent in _tqdm(
                    builder.magnetic_entities,
                    desc="Setup perturbations for rotated hamiltonian",
                ):
                    # fill up the perturbed potentials (for now) based on the on-site projections
                    mag_ent._Vu1_tmp.append(
                        onsite_projection(
                            Vu1, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                        )
                    )
                    mag_ent._Vu2_tmp.append(
                        onsite_projection(
                            Vu2, mag_ent._spin_box_indices, mag_ent._spin_box_indices
                        )
                    )

            if builder.spin_model == "isotopic-only":
                for pair in builder.pairs:
                    pair.energies = np.array(
                        [
                            [
                                interaction_energy(
                                    pair.M1._Vu1_tmp,
                                    pair.M2._Vu1_tmp,
                                    pair._Gij_tmp,
                                    pair._Gji_tmp,
                                    builder.contour.weights,
                                )
                            ]
                        ]
                    )
            else:
                # calculate energies in the current reference hamiltonian direction
                for mag_ent in builder.magnetic_entities:
                    mag_ent.calculate_energies(
                        builder.contour.weights,
                        append=True,
                        third_direction=builder.spin_model == "generalised-grogu",
                    )
                for pair in builder.pairs:
                    pair.calculate_energies(builder.contour.weights, append=True)

            # if we want to keep all the information for some reason we can do it
            if not builder.low_memory_mode:
                builder._rotated_hamiltonians.append(rot_H)
                for mag_ent in builder.magnetic_entities:
                    mag_ent._Vu1.append(mag_ent._Vu1_tmp)
                    mag_ent._Vu2.append(mag_ent._Vu2_tmp)
                    mag_ent._Gii.append(mag_ent._Gii_tmp)
                for pair in builder.pairs:
                    pair._Gij.append(pair._Gij_tmp)
                    pair._Gji.append(pair._Gji_tmp)
            # or fill with empty stuff
            else:
                for mag_ent in builder.magnetic_entities:
                    mag_ent._Vu1.append([])
                    mag_ent._Vu2.append([])
                    mag_ent._Gii.append([])
                for pair in builder.pairs:
                    pair._Gij.append([])
                    pair._Gji.append([])

                # rotate back hamiltonian for the original DFT orientation
                rot_H.rotate(rot_H.scf_xcf_orientation)

        # finalize energies of the magnetic entities and pairs
        # calculate magnetic parameters
        for mag_ent in builder.magnetic_entities:
            # delete temporary stuff
            del mag_ent._Gii_tmp
            del mag_ent._Vu1_tmp
            del mag_ent._Vu2_tmp

            if builder.apply_spin_model:
                if builder.spin_model == "generalised-fit":
                    mag_ent.fit_anisotropy_tensor(builder.ref_xcf_orientations)
                elif builder.spin_model == "generalised-grogu":
                    mag_ent.calculate_anisotropy()
                else:
                    pass

        for pair in builder.pairs:
            # delete temporary stuff
            del pair._Gij_tmp
            del pair._Gji_tmp

            if builder.apply_spin_model:
                if builder.spin_model == "generalised-fit":
                    pair.fit_exchange_tensor(builder.ref_xcf_orientations)
                elif builder.spin_model == "generalised-grogu":
                    pair.calculate_exchange_tensor()
                elif builder.spin_model == "isotropic-only":
                    pair.calculate_isotropic_only()
                else:
                    raise Exception(
                        f"Unknown spin model: {builder.spin_model}! Use apply_spin_model=False"
                    )

    def solve_parallel_over_k(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is parallelized over
        k-points. It uses the `greens_function_solver` instance variable which
        controls the solution method over the energy samples. Generally this is
        the fastest solution method for smaller systems.

        Parameters
        ----------
        builder: Builder
            The main grogupy object
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        raise Exception("MPI is not available!")


if __name__ == "__main__":
    pass
