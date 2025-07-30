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

import copy
import warnings
from typing import Union

import numpy as np
import sisl
from numpy.typing import NDArray

from grogupy._core import TAU_X, TAU_Y, TAU_Z, RotMa2b, build_hh_ss, hsk
from grogupy._tqdm import _tqdm
from grogupy.batch.timing import DefaultTimer
from grogupy.config import CONFIG

from .utilities import spin_tracer

if CONFIG.is_GPU:
    import cupy as cp
    from cupy.typing import NDArray as CNDArray

    # Disable memory pool for device memory (GPU)
    cp.cuda.set_allocator(None)
    # Disable memory pool for pinned memory (CPU).
    cp.cuda.set_pinned_memory_allocator(None)


class Hamiltonian:
    """This class contains the data and the methods related to the Hamiltonian and geometry.

    It sets up the instance based on the path to the Hamiltonian of the DFT calculation and
    the DFT exchange orientation.

    Parameters
    ----------
    infile: Union[str, tuple[sisl.physics.Hamiltonian, Union[sisl.physics.DensityMatrix, None]]]
        Path to the .fdf file or the sisl Hamiltonian and Density matrix, DM is optional
    scf_xcf_orientation: Union[list, NDArray]. optional
        The reference orientation, by default [0,0,1]

    Examples
    --------
    Creating a Hamiltonian from the DFT calculation.

    >>> fdf_path = "/Users/danielpozsar/Downloads/Fe3GeTe2/Fe3GeTe2.fdf"
    >>> scf_xcf_orientation = np.array([0,0,1])
    >>> hamiltonian = Hamiltonian(fdf_path, scf_xcf_orientation)
    >>> print(hamiltonian)
    <grogupy.Hamiltonian scf_xcf_orientation=[0 0 1], orientation=[0 0 1], NO=84>

    Methods
    -------
    extract_exchange_field() :
        Extracts the exchange field and time reversal symmetric and breaking parts
    rotate(orientation) :
        It rotates the exchange field of the Hamiltonian.
    HkSk(k) :
        Sets up the Hamiltonian and the overlap matrix at a given k-point.
    copy() :
        Return a copy of this Pair

    Attributes
    ----------
    _dh: sisl.physics.Hamiltonian
        The sisl Hamiltonian
    _ds: Union[sisl.physics.DensityMatrix, None]
        The sisl density matrix or None if it is not given
    infile: str
        The path to the .fdf file
    H: NDArray
        Hamiltonian built from the sisl Hamiltonian
    S: NDArray
        Overlap matrix built from the sisl Hamiltonian
    scf_xcf_orientation: NDArray
        Orientation of the DFT exchange field
    orientation: NDArray
        Current orientation of the XCF filed
    NO: int
        Number of orbitals in the Hamiltonian
    cell: NDArray
        The unit cell vectors
    nsc: NDArray
        Number of supercells in each direction
    sc_off: NDArray
        Supercell indices
    uc_in_sc_index: int
        Unit cell index
    H_uc: NDArray
        Unit cell Hamiltonian
    times: grogupy.batch.timing.DefaultTimer
        It contains and measures runtime
    """

    number_of_hamiltonians = 0

    def __init__(
        self,
        infile: Union[
            str,
            tuple[sisl.physics.Hamiltonian, Union[sisl.physics.DensityMatrix, None]],
        ],
        scf_xcf_orientation: Union[list, NDArray] = np.array([0, 0, 1]),
    ) -> None:
        """Initialize hamiltonian"""

        self.times: DefaultTimer = DefaultTimer()
        if isinstance(infile, str):
            # get sisl sile
            sile = sisl.get_sile(infile)
            # load hamiltonian
            self._dh: sisl.physics.Hamiltonian = sile.read_hamiltonian()
            try:
                self._ds: Union[None, sisl.physics.DensityMatrix] = (
                    sile.read_density_matrix()
                )
            except:
                self._ds: Union[None, sisl.physics.DensityMatrix] = None
            self.infile: str = infile
        elif isinstance(infile, tuple):
            if isinstance(infile[0], sisl.physics.Hamiltonian) and isinstance(
                infile[1], sisl.physics.DensityMatrix
            ):
                self._dh: sisl.physics.Hamiltonian = infile[0]
                self._ds: Union[None, sisl.physics.DensityMatrix] = infile[1]
                self.infile = "Unknown!"
            else:
                raise Exception("Not valid input:", (type(infile[0]), type(infile[1])))
        else:
            raise Exception("Not valid input:", type(infile))
        # if the Hamiltonian is unpolarized then there is no spin information
        if self._dh.spin.kind not in {1, 2, 3}:
            raise Exception("Unpolarized DFT calculation cannot be used!")
        if self._dh.spin.kind == 1:
            self._spin_state: str = "POLARIZED"
        if self._dh.spin.kind == 2:
            self._spin_state: str = "NON-COLINEAR"
        if self._dh.spin.kind == 3:
            self._spin_state: str = "SPIN-ORBIT"

        H, S = build_hh_ss(self._dh)
        self.H: NDArray = H
        self.S: NDArray = S
        self.scf_xcf_orientation: NDArray = np.array(scf_xcf_orientation)
        if (self.scf_xcf_orientation != 0).sum() != 1:
            warnings.warn(
                f"Tilted exchange field in the DFT calculation: {self.scf_xcf_orientation}"
            )

        self.orientation: NDArray = np.array(self.scf_xcf_orientation)

        # pre calculate hidden unuseed properties
        # they are here so they are dumped to the self.__dict__ upon saving
        self.__no = self._dh.no
        self.__cell = self._dh.geometry.cell
        self.__sc_off = self._dh.geometry.sc_off
        self.__uc_in_sc_index = self._dh.lattice.sc_index([0, 0, 0])

        self.times.measure("setup", restart=True)
        Hamiltonian.number_of_hamiltonians += 1

    def __getstate__(self):
        state = self.__dict__.copy()
        state["times"] = state["times"].__getstate__()
        return state

    def __setstate__(self, state):
        times = object.__new__(DefaultTimer)
        times.__setstate__(state["times"])
        state["times"] = times

        self.__dict__ = state

    def __eq__(self, value):
        if isinstance(value, Hamiltonian):
            if (
                np.allclose(self._dh.Hk().toarray(), value._dh.Hk().toarray())
                and np.allclose(self._dh.Sk().toarray(), value._dh.Sk().toarray())
                and self.infile == value.infile
                and self._spin_state == value._spin_state
                and np.allclose(self.H, value.H)
                and np.allclose(self.S, value.S)
                and np.allclose(self.scf_xcf_orientation, value.scf_xcf_orientation)
                and np.allclose(self.orientation, value.orientation)
            ):
                # if DM is None return True
                if self._ds is None and value._ds is None:
                    return True
                # if DM is not None, then compare
                else:
                    if np.allclose(
                        self._ds.Dk().toarray(), value._ds.Dk().toarray()
                    ) and np.allclose(
                        self._ds.Sk().toarray(), value._ds.Sk().toarray()
                    ):
                        return True
                    else:
                        return False
            return False
        return False

    def __repr__(self) -> str:
        """String representation of the instance."""

        out = f"<grogupy.Hamiltonian scf_xcf_orientation={self.scf_xcf_orientation}, orientation={self.orientation}, NO={self.NO}>"

        return out

    @property
    def geometry(self) -> sisl.geometry.Geometry:
        return self._dh.geometry

    @property
    def NO(self) -> int:
        try:
            self.__no = self._dh.no * 2
        except:
            warnings.warn(
                "Property could not be calculated. This is only acceptable for loaded Hamiltonian!"
            )
        return self.__no

    @property
    def cell(self) -> NDArray:
        try:
            self.__cell = self._dh.geometry.cell
        except:
            warnings.warn(
                "Property could not be calculated. This is only acceptable for loaded Hamiltonian!"
            )
        return self.__cell

    @property
    def nsc(self) -> NDArray:
        return self._dh.geometry.nsc

    @property
    def sc_off(self) -> NDArray:
        try:
            self.__sc_off = self._dh.geometry.sc_off
        except:
            warnings.warn(
                "Property could not be calculated. This is only acceptable for loaded Hamiltonian!"
            )
        return self.__sc_off

    @property
    def uc_in_sc_index(self) -> int:
        self.__uc_in_sc_index = self._dh.sc_index([0, 0, 0])
        return self.__uc_in_sc_index

    @property
    def H_uc(self) -> NDArray:
        return self.H[self.uc_in_sc_index]

    def extract_exchange_field(self) -> tuple[NDArray, NDArray, NDArray, NDArray]:
        """Extract the exchange field and other useful quantities.

        Returns
        -------
        hTRS: NDArray
            Time reversal symmetric part of the Hamiltonian
        hTRB: NDArray
            Time reversal broken symmetric part of the Hamiltonian
        XCF: NDArray
            Exchange field
        H_XCF: NDArray
            Exchange Hamiltonian

        Raises
        ------
        ValueError
            Exchange field has non negligible scalar part.
        """

        # progress bar
        bar = _tqdm(
            None, total=3 + 2 * self.nsc.prod(), desc="Extracting exchange field"
        )

        if CONFIG.is_CPU:
            # identifying TRS and TRB parts of the Hamiltonian
            TAUY: NDArray = np.kron(np.eye(int(self.NO / 2)), TAU_Y)

            hTR: list = []
            for i in range(self.nsc.prod()):
                hTR.append(TAUY @ self.H[i].conj() @ TAUY)
                bar.update()
            hTR = np.array(hTR)

            hTRS: NDArray = (self.H + hTR) / 2
            hTRB: NDArray = (self.H - hTR) / 2

            # extracting the exchange field
            traced: list = []
            for i in range(self.nsc.prod()):
                traced.append(spin_tracer(hTRB[i]))
                bar.update()

            XCF: NDArray = np.array(
                [
                    np.array([f["x"] / 2 for f in traced]),
                    np.array([f["y"] / 2 for f in traced]),
                    np.array([f["z"] / 2 for f in traced]),
                ]
            )

            H_XCF: NDArray = np.zeros(
                (self.nsc.prod(), self.NO, self.NO), dtype="complex128"
            )
            for i, tau in enumerate([TAU_X, TAU_Y, TAU_Z]):
                H_XCF += np.kron(XCF[i], tau)
                bar.update()

        elif CONFIG.is_GPU:
            # identifying TRS and TRB parts of the Hamiltonian
            TAUY: "CNDArray" = cp.kron(cp.eye(int(self.NO / 2)), cp.array(TAU_Y))

            tmp: list = []
            for i in range(self.nsc.prod()):
                tmp.append((TAUY @ cp.array(self.H[i]).conj() @ TAUY).get())
                bar.update()
            hTR: NDArray = np.array(tmp)

            # release this from memory
            TAUY = None

            hTRS: NDArray = (self.H + hTR) / 2
            hTRB: NDArray = (self.H - hTR) / 2

            # extracting the exchange field equation 77
            traced: list = []
            for i in range(self.nsc.prod()):
                traced.append(spin_tracer(hTRB[i]))
                bar.update()

            XCF: "CNDArray" = cp.array(
                [
                    cp.array([f["x"] / 2 for f in traced]),
                    cp.array([f["y"] / 2 for f in traced]),
                    cp.array([f["z"] / 2 for f in traced]),
                ]
            )

            H_XCF: NDArray = np.zeros(
                (self.nsc.prod(), self.NO, self.NO), dtype="complex128"
            )
            for i, tau in enumerate([TAU_X, TAU_Y, TAU_Z]):
                H_XCF += cp.kron(XCF[i], cp.array(tau)).get()
                bar.update()

            XCF, H_XCF = XCF.get(), H_XCF
        else:
            raise ValueError(f"Unknown architecture: {CONFIG.architecture}")

        # check if exchange field has scalar part
        max_xcfs: float = abs(np.array([f["c"] / 2 for f in traced])).max()
        if max_xcfs > 1e-12:
            warnings.warn(
                f"Exchange field has non negligible scalar part. Largest value is {max_xcfs}"
            )
        return hTRS, hTRB, XCF, H_XCF

    def rotate(self, orientation: Union[NDArray, list]) -> None:
        """It rotates the exchange field of the Hamiltonian.

        It dumps the solutions to the `H` and `orientation`
        properties.

        Parameters
        ----------
        orientation: Union[NDArray, list]
            The rotation where it rotates
        """

        orientation = np.array(orientation)

        hTRS, hTRB, XCF, H_XCF = self.extract_exchange_field()
        # obtain rotated exchange field and Hamiltonian
        R: NDArray = RotMa2b(self.orientation, orientation)
        XCF: NDArray = np.einsum("ij,jklm->iklm", R, XCF)

        if CONFIG.is_CPU:
            H_XCF: NDArray = np.zeros(
                (self.nsc.prod(), self.NO, self.NO), dtype=np.complex128
            )
            for i, tau in _tqdm(
                enumerate([TAU_X, TAU_Y, TAU_Z]),
                total=3,
                desc="Rotating Exchange field",
            ):
                H_XCF += np.kron(XCF[i], tau)
        elif CONFIG.is_GPU:
            H_XCF: "CNDArray" = cp.zeros(
                (self.nsc.prod(), self.NO, self.NO), dtype=np.complex128
            )
            XCF = cp.array(XCF)
            for i, tau in _tqdm(
                enumerate([TAU_X, TAU_Y, TAU_Z]),
                total=3,
                desc="Rotating Exchange field",
            ):
                H_XCF += cp.kron(XCF[i], cp.array(tau))
            H_XCF = H_XCF.get()
        else:
            raise Exception(f"Unknown architecture: {CONFIG.architecture}")

        # obtain total Hamiltonian with the rotated exchange field
        self.H: NDArray = hTRS + H_XCF  # equation 76
        self.orientation = orientation

    def HkSk(self, k: tuple = (0, 0, 0)) -> tuple[NDArray, NDArray]:
        """Sets up the Hamiltonian and the overlap matrix at a given k-point.

        Parameters
        ----------
        k: tuple, optional
            The given k-point, by default (0, 0, 0)

        Returns
        -------
        Hk: NDArray
            The Hamiltonian at the given k point
        Sk: NDArray
            The Ovelap matrix at the given k point

        """

        return hsk(self.H, self.S, self.sc_off, k)

    def copy(self):
        """Returns the deepcopy of the instance.

        Returns
        -------
        Hamiltonian
            The copied instance.
        """

        return copy.deepcopy(self)


if __name__ == "__main__":
    pass
