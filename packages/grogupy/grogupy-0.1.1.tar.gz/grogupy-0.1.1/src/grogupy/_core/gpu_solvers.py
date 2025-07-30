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

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Union

import numpy as np
from numpy.typing import NDArray

from grogupy._tqdm import _tqdm
from grogupy.config import CONFIG
from grogupy.physics.utilities import interaction_energy

from .utilities import calc_Vu, onsite_projection, tau_u

if TYPE_CHECKING:
    from grogupy.physics.builder import Builder

if CONFIG.is_GPU:
    # initialize parallel GPU stuff
    import cupy as cp
    from cupy.typing import NDArray as CNDArray

    # Disable memory pool for device memory (GPU)
    cp.cuda.set_allocator(None)
    # Disable memory pool for pinned memory (CPU).
    cp.cuda.set_pinned_memory_allocator(None)

    def gpu_solver(
        max_g_per_loop: int,
        mode: str,
        gpu_number: int,
        kpoints: list[NDArray],
        kweights: list[NDArray],
        SBI: NDArray,
        SBI1: NDArray,
        SBI2: NDArray,
        Ruc: NDArray,
        sc_off: NDArray,
        samples: NDArray,
        G_mag: NDArray,
        G_pair_ij: NDArray,
        G_pair_ji: NDArray,
        rotated_H: NDArray,
        S: NDArray,
        rot_num: Union[int, str] = "Unknown",
    ) -> tuple["CNDArray", "CNDArray", "CNDArray"]:
        """Parallelizes the Green's function solution on GPU.

        Should be used on large systems.

        Parameters
        ----------
        max_g_per_loop: int
            Maximum number of greens function samples per loop
        mode : str
            The Greens function solver, which can be parallel or sequential
        gpu_number : int
            The ID of the GPU which we want to run on
        kpoints : list[NDArray]
            The kpoints already split for the GPUs
        kweights : list[NDArray]
            The kpoint weights already split for the GPUs
        SBI : list[NDArray]
            Spin box indices for the magnetic entities
        SBI1 : list[NDArray]
            Spin box indices for the pairs
        SBI2 : list[NDArray]
            Spin box indices for the pairs
        Ruc : list[NDArray]
            Unit cell shift of the pairs
        sc_off : NDArray
            List of unit cell shifts for unit cell indexes
        samples : NDArray
            Energy samples
        G_mag : list[NDArray]
            Empty container for the final Green's function on each magnetic entity
        G_pair_ij : list[NDArray]
            Empty container for the final Green's function on each pair
        G_pair_ji : list[NDArray]
            Empty container for the final Green's function on each pair
        rotated_H : list[NDArray]
            Hamiltonian with rotated exchange field
        S : NDArray
            Overlap matrix, should be the same for all Hamiltonians
        rot_num: str, optional
            Rotation number for tqdm print, by default "Unknown"

        Returns
        -------
        local_G_mag : CNDArray
            The Greens function of the mangetic entities
        local_G_pair_ij : CNDArray
            The Greens function from mangetic entity i to j on the given GPU
        local_G_pair_ji : CNDArray
            The Greens function from mangetic entity j to i on the given GPU
        """

        # use the specified GPU
        with cp.cuda.Device(gpu_number):
            # copy everything to GPU
            kpoints = cp.array(kpoints[gpu_number])
            kweights = cp.array(kweights[gpu_number])
            SBI = cp.array(SBI)
            SBI1 = cp.array(SBI1)
            SBI2 = cp.array(SBI2)
            supercell_shift = cp.array(Ruc)

            sc_off = cp.array(sc_off)
            eset = samples.shape[0]
            samples = cp.array(samples.reshape(eset, 1, 1))

            G_mag = np.zeros_like(G_mag)
            G_pair_ij = np.zeros_like(G_pair_ij)
            G_pair_ji = np.zeros_like(G_pair_ji)

            for i in _tqdm(
                range(len(kpoints)),
                desc=f"Rotation {rot_num}, parallel over k on GPU{gpu_number+1}",
            ):
                # weight of k point in BZ integral
                wk = kweights[i]
                k = kpoints[i]

                # calculate Hamiltonian and Overlap matrix in a given k point
                # this generates the list of phases
                phases = cp.exp(-1j * 2 * cp.pi * k @ sc_off.T)
                # phases applied to the hamiltonian
                HK = cp.einsum("abc,a->bc", cp.array(rotated_H), phases)
                SK = cp.einsum("abc,a->bc", cp.array(S), phases)

                # solve the Greens function on all energy points in one step
                if mode[0].lower() == "p":
                    Gk = cp.linalg.inv(SK * samples - HK)

                    # store the Greens function slice of the magnetic entities
                    for l, sbi in enumerate(SBI):
                        G_mag[l] += (onsite_projection(Gk, sbi, sbi) * wk).get()

                    # store the Greens function slice of the pairs
                    for l, dat in enumerate(zip(SBI1, SBI2, supercell_shift)):
                        sbi1, sbi2, ruc = dat
                        phase = cp.exp(1j * 2 * cp.pi * k @ ruc.T)

                        G_pair_ij[l] += (
                            onsite_projection(Gk, sbi1, sbi2) * wk * phase
                        ).get()
                        G_pair_ji[l] += (
                            onsite_projection(Gk, sbi2, sbi1) * wk / phase
                        ).get()

                # solve Greens function sequentially for the energies, because of memory bound
                elif mode[0].lower() == "s":

                    # make chunks for reduced parallelization over energy sample points
                    number_of_chunks = np.floor(eset / max_g_per_loop) + 1

                    # constrain to sensible size
                    if number_of_chunks > eset:
                        number_of_chunks = eset

                    # create batches using slices on every instance
                    slices = np.array_split(range(eset), number_of_chunks)

                    # fills the holders sequentially by the Greens function slices on
                    # a given energy
                    for slice in slices:
                        Gk = cp.linalg.inv(SK * samples[slice] - HK)

                        # store the Greens function slice of the magnetic entities
                        for l, sbi in enumerate(SBI):
                            G_mag[l][slice] += (
                                onsite_projection(Gk, sbi, sbi) * wk
                            ).get()

                        # store the Greens function slice of the pairs
                        for l, dat in enumerate(zip(SBI1, SBI2, Ruc)):
                            sbi1, sbi2, ruc = dat
                            phase = cp.exp(1j * 2 * cp.pi * k @ ruc.T)

                            G_pair_ij[l][slice] += (
                                onsite_projection(Gk, sbi1, sbi2) * wk * phase
                            ).get()
                            G_pair_ji[l][slice] += (
                                onsite_projection(Gk, sbi2, sbi1) * wk / phase
                            ).get()

        return G_mag, G_pair_ij, G_pair_ji

    def solve_parallel_over_k(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is parallelized over
        k-points. It uses the number of GPUs given. And determines the parallelization
        over energy levels from the ``builder.greens_function_solver`` attribute.

        Parameters
        ----------
        builder : Builder
            The system that we want to solve
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        parallel_size = CONFIG.parallel_size

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
            print(f"Memory allocated by rotated Hamilonian: {H_mem/1e6} MB")
            print(f"Memory allocated by magnetic entities: {mag_ent_mem/1e6} MB")
            print(f"Memory allocated by pairs: {pair_mem/1e6} MB")
            print(
                f"Total memory allocated in RAM: {(H_mem+mag_ent_mem+pair_mem) / 1e6} MB"
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

            print("Memory allocated on GPU:")
            print(f"Memory allocated by rotated Hamilonian: {H_mem/1e6} MB")
            print(f"Memory allocated for Greens function samples: {G_mem/1e6} MB")
            # 25 is the maximum amount of memory used for matrix inversion
            gpu_max_mem = np.max([mag_ent_mem + pair_mem + H_mem, G_mem * 25]) / 1e6
            print(f"Total peak memory on GPU during solution: {gpu_max_mem} MB")
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
            parallel_k = np.array_split(builder.kspace.kpoints, parallel_size)
            parallel_w = np.array_split(builder.kspace.weights, parallel_size)
            with ThreadPoolExecutor(max_workers=parallel_size) as executor:
                futures = [
                    executor.submit(
                        gpu_solver,
                        builder.max_g_per_loop,
                        builder.greens_function_solver,
                        gpu_number,
                        parallel_k,
                        parallel_w,
                        builder.magnetic_entities.SBI,
                        builder.pairs.SBI1,
                        builder.pairs.SBI2,
                        builder.pairs.supercell_shift,
                        builder.hamiltonian.sc_off,
                        builder.contour.samples,
                        builder.magnetic_entities._Gii_tmp,
                        builder.pairs._Gij_tmp,
                        builder.pairs._Gji_tmp,
                        builder.hamiltonian.H,
                        builder.hamiltonian.S,
                        i + 1,
                    )
                    for gpu_number in range(parallel_size)
                ]
                results = [future.result() for future in futures]

            # Combine results
            G_mag_reduce = np.zeros_like(builder.magnetic_entities._Gii_tmp)
            G_pair_ij_reduce = np.zeros_like(builder.pairs._Gij_tmp)
            G_pair_ji_reduce = np.zeros_like(builder.pairs._Gji_tmp)
            for G_mag_local, G_pair_ij_local, G_pair_ji_local in results:
                G_mag_reduce += G_mag_local
                G_pair_ij_reduce += G_pair_ij_local
                G_pair_ji_reduce += G_pair_ji_local

            for i, mag_ent in enumerate(builder.magnetic_entities):
                mag_ent._Gii_tmp = G_mag_reduce[i]

            for i, pair in enumerate(builder.pairs):
                pair._Gij_tmp = G_pair_ij_reduce[i]
                pair._Gji_tmp = G_pair_ji_reduce[i]

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

    def gpu_solver(
        max_g_per_loop: int,
        mode: str,
        gpu_number: int,
        kpoints: list[NDArray],
        kweights: list[NDArray],
        SBI: NDArray,
        SBI1: NDArray,
        SBI2: NDArray,
        Ruc: NDArray,
        sc_off: NDArray,
        samples: NDArray,
        G_mag: NDArray,
        G_pair_ij: NDArray,
        G_pair_ji: NDArray,
        rotated_H: NDArray,
        S: NDArray,
        rot_num: Union[int, str] = "Unknown",
    ) -> tuple["CNDArray", "CNDArray", "CNDArray"]:
        """Parallelizes the Green's function solution on GPU.

        Should be used on large systems.

        Parameters
        ----------
        max_g_per_loop: int
            Maximum number of greens function samples per loop
        mode : str
            The Greens function solver, which can be parallel or sequential
        gpu_number : int
            The ID of the GPU which we want to run on
        kpoints : list[NDArray]
            The kpoints already split for the GPUs
        kweights : list[NDArray]
            The kpoint weights already split for the GPUs
        SBI : list[NDArray]
            Spin box indices for the magnetic entities
        SBI1 : list[NDArray]
            Spin box indices for the pairs
        SBI2 : list[NDArray]
            Spin box indices for the pairs
        Ruc : list[NDArray]
            Unit cell shift of the pairs
        sc_off : NDArray
            List of unit cell shifts for unit cell indexes
        samples : NDArray
            Energy samples
        G_mag : list[NDArray]
            Empty container for the final Green's function on each magnetic entity
        G_pair_ij : list[NDArray]
            Empty container for the final Green's function on each pair
        G_pair_ji : list[NDArray]
            Empty container for the final Green's function on each pair
        rotated_H : list[NDArray]
            Hamiltonian with rotated exchange field
        S : NDArray
            Overlap matrix, should be the same for all Hamiltonians
        rot_num: str, optional
            Rotation number for tqdm print, by default "Unknown"

        Returns
        -------
        local_G_mag : CNDArray
            The Greens function of the mangetic entities
        local_G_pair_ij : CNDArray
            The Greens function from mangetic entity i to j on the given GPU
        local_G_pair_ji : CNDArray
            The Greens function from mangetic entity j to i on the given GPU
        """

        raise Exception("GPU is not available!")

    def solve_parallel_over_k(builder: "Builder", print_memory: bool = False) -> None:
        """It calculates the energies by the Greens function method.

        It inverts the Hamiltonians of all directions set up in the given
        k-points at the given energy levels. The solution is parallelized over
        k-points. It uses the number of GPUs given. And determines the parallelization
        over energy levels from the ``builder.greens_function_solver`` attribute.

        Parameters
        ----------
        builder : Builder
            The system that we want to solve
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        raise Exception("GPU is not available!")


if __name__ == "__main__":
    pass
