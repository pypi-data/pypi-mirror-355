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
import io
import os
import warnings
from typing import Union

import numpy as np
import sisl
from numpy.typing import NDArray

from grogupy import __version__
from grogupy._core.utilities import process_ref_directions, setup_from_range
from grogupy._tqdm import _tqdm
from grogupy.batch.timing import DefaultTimer
from grogupy.config import CONFIG

from .contour import Contour
from .hamiltonian import Hamiltonian
from .kspace import Kspace
from .magnetic_entity import MagneticEntity, MagneticEntityList
from .pair import Pair, PairList

try:
    import pytest

    @pytest.fixture()
    def setup():
        k, c = Kspace(), Contour(100, 100, -20)
        h = Hamiltonian(
            "/Users/danielpozsar/Downloads/Fe3GeTe2/Fe3GeTe2.fdf",
            [0, 0, 1],
        )
        return k, c, h

except:
    pass


class Builder:
    """This class contains the data and the methods related to the Simulation.

    Parameters
    ----------
    ref_xcf_orientations: Union[list[list[Union[int, float]]], NDArray[Union[np.int64, np.float64]], dict[str, Union[NDArray[Union[np.int64, np.float64]], list[float]]]], optional
        The reference directions. The perpendicular directions are created by rotating
        the x,y,z frame to the given reference directions, by default [[1,0,0], [0,1,0], [0,0,1]]

    Examples
    --------
    Creating a Simulation from the DFT exchange field orientation,  Hamiltonian, Kspace
    and Contour.

    >>> kspace, contour, hamiltonian = getfixture('setup')
    >>> simulation = Builder(np.array([[1,0,0], [0,1,0], [0,0,1]]))
    >>> simulation.add_kspace(kspace)
    >>> simulation.add_contour(contour)
    >>> simulation.add_hamiltonian(hamiltonian)
    >>> simulation
    <grogupy.Builder npairs=0, numk=1, kset=[1 1 1], eset=100>

    Methods
    -------
    add_kspace(kspace) :
        Adds the k-space information to the instance.
    add_contour(contour) :
        Adds the energy contour information to the instance.
    add_hamiltonian(hamiltonian) :
        Adds the Hamiltonian and geometrical information to the instance.
    add_magnetic_entities(magnetic_entities) :
        Adds a MagneticEntity or a list of MagneticEntity to the instance.
    add_pairs(pairs) :
        Adds a Pair or a list of Pair to the instance.
    create_magnetic_entities(magnetic_entities) :
        Creates a list of MagneticEntity from a list of dictionaries.
    create_pairs(pairs) :
        Creates a list of Pair from a list of dictionaries.
    solve() :
        Wrapper for Greens function solver.
    to_magnopy(): str
        The magnopy output file as a string
    save_magnopy(outfile) :
        Creates a magnopy input file based on a path.
    save_pickle(outfile) :
        It dumps the simulation parameters to a pickle file.
    copy() :
        Return a copy of this Pair

    Attributes
    ----------
    infile: str
        Input path to the .fdf file
    scf_xcf_orientation: NDArray
        The DFT exchange filed orientation from the instance Hamiltonian
    ref_xcf_orientations: list[dict]
        The reference directions and two perpendicular direction. Every element is a
        dictionary, wth two elements, 'o', the reference direction and 'vw', the two
        perpendicular directions and a third direction that is the linear combination of
        the two
    kspace: Union[None, Kspace]
        The k-space part of the integral
    contour: Union[None, Contour]
        The energy part of the integral
    hamiltonian: Union[None, Hamiltonian]
        The Hamiltonian of the previous article
    magnetic_entities: MagneticEntityList
        List of magnetic entities
    pairs: PairList
        List of pairs
    low_memory_mode: bool, optional
        The memory mode of the calculation, by default False
    greens_function_solver: {"Sequential", "Parallel"}
        The solution method for the Hamiltonian inversion, by default "Parallel"
    max_g_per_loop: int, optional
        Maximum number of greens function samples per loop, by default 1
    apply_spin_model: bool, optional
        If it is True, then the exchange and anisotropy tensors are calculated,
        by default True
    spin_model: {"generalised-fit", "generalised-grogu", "isotropic-only"}
        The solution method for the exchange and anisotropy tensor, by default
        "generalised-fit"
    parallel_mode: Union[None, str], optional
        The parallelization mode for the Hamiltonian inversions, by default None
    architecture: {"CPU", "GPU"}, optional
        The architecture of the machine that grogupy is run on, by default 'CPU'
    SLURM_ID: str
        The ID of the SLURM job, if available, else 'Could not be determined.'
    _dh: sisl.physics.Hamiltonian
        The sisl Hamiltonian from the instance Hamiltonian
    times: grogupy.batch.timing.DefaultTimer
        It contains and measures runtime
    """

    root_node = 0

    def __init__(
        self,
        ref_xcf_orientations: Union[list[list[float]], NDArray, list[dict]] = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ],
    ) -> None:
        """Initialize simulation."""

        #: Contains a DefaultTimer instance to measure runtime
        self.times: DefaultTimer = DefaultTimer()
        #: Contains a Kspace instance
        self.kspace: Union[None, Kspace] = None
        #: Contains a Contour instance
        self.contour: Union[None, Contour] = None
        #: Contains a Hamiltonian instance
        self.hamiltonian: Union[None, Hamiltonian] = None

        #: The list of magnetic entities
        self.magnetic_entities: MagneticEntityList = MagneticEntityList()
        #: The list of pairs
        self.pairs: PairList = PairList()

        # these are the relevant parameters for the solver
        self.__low_memory_mode: bool = False
        self.__greens_function_solver: str = "Parallel"
        self.__max_g_per_loop: int = 1
        self.__parallel_mode: Union[None, str] = None
        self.__architecture: str = CONFIG.architecture
        self.__apply_spin_model: bool = True
        self.__spin_model: str = "generalised-grogu"

        # create reference directions
        self.ref_xcf_orientations = process_ref_directions(
            ref_xcf_orientations,
            self.spin_model,
        )

        self._rotated_hamiltonians: list[Hamiltonian] = []

        try:
            self.SLURM_ID: str = os.environ["SLURM_JOB_ID"]
        except:
            self.SLURM_ID: str = "Could not be determined."

        self.__version = __version__

        self.times.measure("setup", restart=True)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["times"] = state["times"].__getstate__()
        state["contour"] = state["contour"].__getstate__()
        state["kspace"] = state["kspace"].__getstate__()
        state["hamiltonian"] = state["hamiltonian"].__getstate__()
        state["magnetic_entities"] = state["magnetic_entities"].__getstate__()
        state["pairs"] = state["pairs"].__getstate__()

        out = []
        for h in state["_rotated_hamiltonians"]:
            out.append(h.__getstate__())
        state["_rotated_hamiltonians"] = out

        return state

    def __setstate__(self, state):
        times = object.__new__(DefaultTimer)
        times.__setstate__(state["times"])
        state["times"] = times

        contour = object.__new__(Contour)
        contour.__setstate__(state["contour"])
        state["contour"] = contour

        kspace = object.__new__(Kspace)
        kspace.__setstate__(state["kspace"])
        state["kspace"] = kspace

        hamiltonian: Hamiltonian = object.__new__(Hamiltonian)
        hamiltonian.__setstate__(state["hamiltonian"])
        state["hamiltonian"] = hamiltonian

        magnetic_entities = object.__new__(MagneticEntityList)
        magnetic_entities.__setstate__(state["magnetic_entities"])
        state["magnetic_entities"] = magnetic_entities

        pairs = object.__new__(PairList)
        pairs.__setstate__(state["pairs"])
        state["pairs"] = pairs

        out = []
        for h in state["_rotated_hamiltonians"]:
            temp = object.__new__(Hamiltonian)
            temp.__setstate__(h)
            out.append(temp)
        state["_rotated_hamiltonians"] = out

        self.__dict__ = state

    def __eq__(self, value):
        if isinstance(value, Builder):
            if (
                self.times == value.times
                and self.kspace == value.kspace
                and self.contour == value.contour
                and self.hamiltonian == value.hamiltonian
                and self.__low_memory_mode == value.__low_memory_mode
                and self.__greens_function_solver == value.__greens_function_solver
                and self.__max_g_per_loop == value.__max_g_per_loop
                and self.__parallel_mode == value.__parallel_mode
                and self.__architecture == value.__architecture
                and self.__spin_model == value.__spin_model
                and self.SLURM_ID == value.SLURM_ID
                and self.__version == value.__version
            ):
                if len(self._rotated_hamiltonians) != len(value._rotated_hamiltonians):
                    return False
                if len(self.magnetic_entities) != len(value.magnetic_entities):
                    return False
                if len(self.pairs) != len(value.pairs):
                    return False
                if len(self.ref_xcf_orientations) != len(value.ref_xcf_orientations):
                    return False

                for i in range(len(self.ref_xcf_orientations)):
                    for k in self.ref_xcf_orientations[i].keys():
                        if not np.allclose(
                            self.ref_xcf_orientations[i][k],
                            value.ref_xcf_orientations[i][k],
                        ):
                            return False

                for one, two in zip(
                    self._rotated_hamiltonians, value._rotated_hamiltonians
                ):
                    if one != two:
                        return False

                for one, two in zip(self.magnetic_entities, value.magnetic_entities):
                    if one != two:
                        return False

                for one, two in zip(self.pairs, value.pairs):
                    if one != two:
                        return False
                return True
            return False
        return False

    def __str__(self) -> str:
        """It prints the parameters and the description of the job.

        Args:
            self :
                It contains the simulations parameters
        """

        section = "========================================"
        newline = "\n"

        out = ""
        out += section + newline
        out += f"grogupy version: {self.__version}" + newline
        out += f"Input file: {self.infile}" + newline
        if self.hamiltonian is not None:
            out += f"Spin mode: {self.hamiltonian._spin_state}" + newline
            out += f"Number of orbitals: {self.hamiltonian.NO}" + newline
        else:
            out += f"Spin mode: Not defined" + newline
            out += f"Number of orbitals: Not defined" + newline
        out += section + newline
        out += f"SLURM job ID: {self.SLURM_ID}" + newline
        out += f"Architecture: {self.__architecture}" + newline
        if self.__architecture == "CPU":
            out += (
                f"Number of threads in the parallel cluster: {CONFIG.parallel_size}"
                + newline
            )
        elif self.__architecture == "GPU":
            out += f"Number of GPUs in the cluster: {CONFIG.parallel_size}" + newline
        if self.parallel_mode is None:
            out += "Parallelization is over: Nothing" + newline
        else:
            out += f"Parallelization is over: {self.parallel_mode}" + newline
        out += (
            f"Solver used for Greens function calculation: {self.greens_function_solver}"
            + newline
        )
        if self.greens_function_solver[0].lower() == "s":
            max_g = self.__max_g_per_loop
        else:
            if self.contour is not None:
                max_g = self.contour.eset
            else:
                max_g = "Not defined"
        out += f"Maximum number of Greens function samples per batch: {max_g}" + newline

        out += f"Spin model: {self.spin_model}" + newline
        out += section + newline

        out += f"Cell [Ang]:" + newline

        if self.hamiltonian is not None:
            bio = io.BytesIO()
            np.savetxt(bio, self.hamiltonian.cell)
            cell = bio.getvalue().decode("latin1")
            out += cell
        else:
            out += "Not defined"

        out += section + newline
        out += f"DFT axis: {self.scf_xcf_orientation}" + newline
        out += "Quantization axis and perpendicular rotation directions:" + newline
        for ref in self.ref_xcf_orientations:
            out += f"{ref['o']} --> {ref['vw']}" + newline

        out += section + newline
        out += "Parameters for the Brillouin zone sampling:" + newline
        if self.kspace is not None:
            out += f"Number of k points: {self.kspace.kset.prod()}" + newline
            out += f"K points in each directions: {self.kspace.kset}" + newline
        else:
            out += f"Number of k points: Not defined" + newline
            out += f"K points in each directions: Not defined" + newline
        out += "Parameters for the contour integral:" + newline
        if self.contour is not None:
            out += f"Eset: {self.contour.eset}" + newline
            out += f"Esetp: {self.contour.esetp}" + newline
            if self.contour.automatic_emin:
                out += (
                    f"Ebot: {self.contour.emin}        WARNING: This was automatically determined!"
                    + newline
                )
            else:
                out += f"Ebot: {self.contour.emin}" + newline
            out += f"Etop: {self.contour.emax}" + newline
        else:
            out += "Not defined"
        out += section + newline

        return out

    def __repr__(self) -> str:
        if self.kspace is None:
            NK = "None"
            kset = "None"
        else:
            NK = self.kspace.NK
            kset = self.kspace.kset
        if self.contour is None:
            eset = "None"
        else:
            eset = self.contour.eset

        string = f"<grogupy.Builder npairs={len(self.pairs)}, numk={NK}, kset={kset}, eset={eset}>"

        return string

    @property
    def NO(self) -> int:
        """The number of orbitals in the Hamiltonian."""

        if self.hamiltonian is None:
            raise Exception("You have to add Hamiltonian first!")

        return self.hamiltonian.NO

    @property
    def spin_model(self) -> str:
        """The solver used for the exchange and anisotropy tensor calculation."""
        return self.__spin_model

    @spin_model.setter
    def spin_model(self, value: str) -> None:
        if value == "generalised-fit":
            self.__spin_model: str = "generalised-fit"
            # if there are more than two perpendicular directions (generalised-grogu)
            # or ther are less than two perpendicular directions (isotropic-only),
            # then generate the perpendicular directions from the reference directions
            for ref_xcf in self.ref_xcf_orientations:
                if len(ref_xcf["vw"]) != 2:
                    process_ref_directions(
                        ref_xcf_orientations=np.array(
                            [ref["o"] for ref in self.ref_xcf_orientations]
                        ),
                        spin_model="generalised-fit",
                    )
                    warnings.warn(
                        "generalised-fit spin model: reset perpendicular directions!"
                    )
                    break

        elif value == "generalised-grogu":
            self.__spin_model: str = "generalised-grogu"
            self.ref_xcf_orientations = [
                dict(o=np.array([1, 0, 0]), vw=np.array([[0, 0, -1], [0, 1, 0]])),
                dict(o=np.array([0, 1, 0]), vw=np.array([[1, 0, 0], [0, 0, -1]])),
                dict(o=np.array([0, 0, 1]), vw=np.array([[1, 0, 0], [0, 1, 0]])),
            ]
            for ref in self.ref_xcf_orientations:
                v = ref["vw"][0]
                w = ref["vw"][1]
                vw = (v + w) / np.linalg.norm(v + w)
                ref["vw"] = np.vstack((ref["vw"], vw))
            warnings.warn(
                "generalised-grogu spin model: reset reference and perpendicular directions!"
            )

        elif value == "isotropic-only":
            self.__spin_model: str = "isotropic-only"
            self.ref_xcf_orientations = [self.ref_xcf_orientations[0]]
            self.ref_xcf_orientations[0]["vw"] = np.array(
                [self.ref_xcf_orientations[0]["vw"][0]]
            )
            warnings.warn(
                "isotropic-only spin model: first reference and first perpendicular direction is used!"
            )

        else:
            raise Exception(f"Unrecognized solution method: {value}")

    @property
    def low_memory_mode(self) -> bool:
        """The memory mode of the calculation."""
        return self.__low_memory_mode

    @low_memory_mode.setter
    def low_memory_mode(self, value: bool) -> None:
        if value == False:
            self.__low_memory_mode = False
        elif value == True:
            self.__low_memory_mode = True
        else:
            raise Exception("This must be Bool!")

    @property
    def apply_spin_model(self) -> bool:
        """If it is True, then the exchange and anisotropy tensors are calculated."""
        return self.__apply_spin_model

    @apply_spin_model.setter
    def apply_spin_model(self, value: bool) -> None:
        if value == False:
            self.__apply_spin_model = False
        elif value == True:
            self.__apply_spin_model = True
        else:
            raise Exception("This must be Bool!")

    @property
    def greens_function_solver(self) -> str:
        """The solution method for the Hamiltonian inversion, by default "Sequential"."""
        return self.__greens_function_solver

    @greens_function_solver.setter
    def greens_function_solver(self, value: str) -> None:
        if value.lower()[0] == "s":
            self.__greens_function_solver = "Sequential"
        elif value.lower()[0] == "p":
            self.__greens_function_solver = "Parallel"
        else:
            raise Exception(
                f"{value} is not a permitted Green's function solver, when the architecture is {self.__architecture}."
            )

    @property
    def max_g_per_loop(self) -> int:
        """Maximum number of greens function samples per loop."""
        return self.__max_g_per_loop

    @max_g_per_loop.setter
    def max_g_per_loop(self, value) -> None:
        if (value - int(value)) < 1e-5 and value >= 0:
            value = int(value)
            self.__max_g_per_loop = value
        else:
            raise Exception("It should be a positive integer.")

    @property
    def parallel_mode(self) -> Union[str, None]:
        """The parallelization mode for the Hamiltonian inversions, by default None."""
        return self.__parallel_mode

    @parallel_mode.setter
    def parallel_mode(self, value) -> None:
        if value is None:
            self.__parallel_mode = None
        elif value[0].lower() == "k":
            self.__parallel_mode = "K"
        else:
            raise Exception(f"Unknown parallel mode: {value}!")

    @property
    def architecture(self) -> str:
        """The architecture of the machine that grogupy is run on, by default 'CPU'."""
        return self.__architecture

    @property
    def _dh(self) -> Union[None, sisl.physics.Hamiltonian]:
        """``sisl`` Hamiltonian object used in the input."""
        if self.hamiltonian is None:
            return None
        else:
            return self.hamiltonian._dh

    @property
    def _ds(self) -> Union[None, sisl.physics.DensityMatrix]:
        """``sisl`` density matrix object used in the input."""
        if self.hamiltonian is None:
            return None
        else:
            return self.hamiltonian._ds

    @property
    def geometry(self) -> Union[None, sisl.geometry.Geometry]:
        """``sisl`` geometry object."""
        if self.hamiltonian is None:
            return None
        else:
            return self.hamiltonian._dh.geometry

    @property
    def scf_xcf_orientation(self) -> Union[None, NDArray]:
        """Exchange field orientation in the DFT calculation."""
        if self.hamiltonian is None:
            return None
        else:
            return self.hamiltonian.scf_xcf_orientation

    @property
    def infile(self) -> Union[None, str]:
        """Input file used to build the Hamiltonian."""
        if self.hamiltonian is None:
            return None
        else:
            return self.hamiltonian.infile

    @property
    def version(self) -> str:
        """Version of grogupy."""
        return self.__version

    def to_magnopy(
        self,
        magnetic_moment: str = "total",
        precision: Union[None, int] = None,
        comments: bool = True,
    ) -> str:
        """Returns the magnopy input file as string.

        It is useful for dumping information to the standard output on
        runtime.

        Parameters
        ----------
        magnetic_moment: str, optional
            It switches the used spin moment in the output, can be 'total'
            for the whole atom or atoms involved in the magnetic entity or
            'local' if we only use the part of the mulliken projections that
            are exactly on the magnetic entity, which may be just a subshell
            of the atom, by default 'total'
        precision: Union[None, int], optional
            The precision of the magnetic parameters in the output, if None
            everything is written, by default None
        comments: bool, optional
            Wether to add comments in the beginning of file, by default True

        Returns
        -------
        str
            Magnopy input file
        """

        if self.apply_spin_model == False:
            raise Exception(
                "Exchange and anisotropy is not calculated! Use apply_spin_model=True"
            )

        if precision is not None:
            if not isinstance(precision, int):
                warnings.warn(
                    f"precision must by an integer, but it is {type(precision)}. It was set to None."
                )
                precision = None
        if precision is None:
            precision = 30

        section = "================================================================================"
        subsection = "--------------------------------------------------------------------------------"
        newline = "\n"

        out = ""
        out += section + newline
        out += "GROGU INFORMATION" + newline
        if comments:
            out += newline
            out += "\n".join(self.__str__().split("\n"))
            out += newline

        out += section + newline
        out += "Hamiltonian convention" + newline
        out += "Double counting      true" + newline
        out += "Normalized spins     true" + newline
        out += "Intra-atomic factor  +1" + newline
        out += "Exchange factor      +0.5" + newline

        out += section + newline
        out += f"Cell (Ang)" + newline
        if self.hamiltonian is not None:
            bio = io.BytesIO()
            np.savetxt(bio, self.hamiltonian.cell)
            cell = bio.getvalue().decode("latin1")
            out += cell
        else:
            raise Exception("Hamiltonian is not defined!")

        out += section + newline
        out += "Magnetic sites" + newline
        out += f"Number of sites {len(self.magnetic_entities)}" + newline
        out += "Name x (Ang) y (Ang) z (Ang) s sx sy sz" + newline
        for mag_ent in self.magnetic_entities:
            out += mag_ent.tag + " "
            out += f"{mag_ent._xyz.mean(axis=0)[0]} {mag_ent._xyz.mean(axis=0)[1]} {mag_ent._xyz.mean(axis=0)[2]} "
            if magnetic_moment[0].lower() == "l":
                out += f"{mag_ent.local_S} {mag_ent.local_Sx} {mag_ent.local_Sy} {mag_ent.local_Sz}"
            else:
                out += f"{mag_ent.total_S} {mag_ent.total_Sx} {mag_ent.total_Sy} {mag_ent.total_Sz}"
            out += newline

        out += section + newline
        out += "Intra-atomic anisotropy tensor (meV)" + newline
        for mag_ent in self.magnetic_entities:
            out += subsection + newline
            out += mag_ent.tag + newline
            if mag_ent.K_meV is not None:
                K = np.around(mag_ent.K_meV, decimals=precision)
            else:
                K = np.around(np.zeros((3, 3)), decimals=precision)
            out += "Matrix" + newline
            out += f"    {K[0,0]} {K[0,1]} {K[0,2]}" + newline
            out += f"    {K[1,0]} {K[1,1]} {K[1,2]}" + newline
            out += f"    {K[2,0]} {K[2,1]} {K[2,2]}" + newline
        out += subsection + newline

        out += section + newline
        out += "Exchange tensor (meV)" + newline
        out += f"Number of pairs {len(self.pairs)}" + newline
        out += subsection + newline
        out += "Name1    Name2    i    j    k    d (Ang)" + newline
        for pair in self.pairs:
            out += subsection + newline
            tag = pair.tags[0] + " " + pair.tags[1]
            out += tag + " " + " ".join(map(str, pair.supercell_shift))
            out += f" {pair.distance}" + newline
            if pair.J_meV is not None:
                J = np.around(pair.J_meV, decimals=precision)
            elif pair.J_iso_meV is not None:
                J = np.around(np.diag(np.ones(3) * pair.J_iso_meV), decimals=precision)
            else:
                raise Exception("Both J and J_iso is None!")
            out += "Matrix" + newline
            out += f"    {J[0,0]} {J[0,1]} {J[0,2]}" + newline
            out += f"    {J[1,0]} {J[1,1]} {J[1,2]}" + newline
            out += f"    {J[2,0]} {J[2,1]} {J[2,2]}" + newline
        out += subsection + newline

        out += section + newline

        return out

    def add_kspace(self, kspace: Kspace) -> None:
        """Adds the k-space information to the instance.

        Parameters
        ----------
        kspace: Kspace
            This class contains the information of the k-space
        """

        if isinstance(kspace, Kspace):
            self.kspace: Union[None, Kspace] = kspace
        else:
            raise Exception(f"Bad type for Kspace: {type(kspace)}")

    def add_contour(self, contour: Contour) -> None:
        """Adds the energy contour information to the instance.

        Parameters
        ----------
        contour: Contour
            This class contains the information of the energy contour
        """

        if isinstance(contour, Contour):
            self.contour: Union[None, Contour] = contour
        else:
            raise Exception(f"Bad type for Contour: {type(contour)}")

    def add_hamiltonian(self, hamiltonian: Hamiltonian) -> None:
        """Adds the Hamiltonian and geometrical information to the instance.

        Parameters
        ----------
        hamiltonian: Hamiltonian
            This class contains the information of the Hamiltonian
        """

        if isinstance(hamiltonian, Hamiltonian):
            self.hamiltonian: Union[None, Hamiltonian] = hamiltonian
        else:
            raise Exception(f"Bad type for Hamiltonian: {type(hamiltonian)}")

    def setup_from_range(
        self,
        R: float,
        subset: Union[
            None, int, str, list[int], list[list[int]], list[str], list[list[str]]
        ] = None,
        **kwargs,
    ) -> None:
        """Generates all the pairs and magnetic entities from atoms in a given radius.

        It takes all the atoms from the unit cell and generates
        all the corresponding pairs and magnetic entities in the given
        radius. It can generate pairs for a subset of of atoms,
        which can be given by the ``subset`` parameter.

        1. If subset is None all atoms can create pairs

        2. If subset is a list of integers, then all the
        possible pairs will be generated to these atoms in
        the unit cell

        3. If subset is two list, then the first list is the
        list of atoms in the unit cell (``Ri``), that can create
        pairs and the second list is the list of atoms outside
        the unit cell that can create pairs (``Rj``)

        !!!WARNING!!!
        In the third case it is really ``Ri`` and ``Rj``, that
        are given, so in some cases we could miss pairs in the
        unit cell.

        Parameters
        ----------
        R : float
            The radius where the pairs are found
        subset : Union[None, int, str, list[int], list[list[int]], list[str], list[list[str]]]
            The subset of atoms that contribute to the pairs, by
            default None

        Other Parameters
        ----------------
        **kwargs: otpional
            These are passed to the magnetic entity dictionary

        """
        if self.hamiltonian is not None:
            magnetic_entities, pairs = setup_from_range(
                self.hamiltonian._dh, R, subset, **kwargs
            )

            self.add_magnetic_entities(magnetic_entities)
            self.add_pairs(pairs)
        else:
            raise Exception("Hamiltonian not defined!")

    def create_magnetic_entities(
        self, magnetic_entities: Union[dict, list[dict]]
    ) -> MagneticEntityList:
        """Creates a list of MagneticEntity from a list of dictionaries.

        The dictionaries must contain an acceptable combination of `atom`, `l` and
        `orb`, based on the accepted input for MagneticEntity. The Hamiltonian is
        taken from the instance Hamiltonian.

        Parameters
        ----------
        magnetic_entities: Union[dict, list[dict]]
            The list of dictionaries or a single dictionary

        Returns
        -------
        MagneticEntityList
            List of MagneticEntity instances

        Raise
        -----
        Exception
            Hamiltonian is not added to the instance
        """

        if self.hamiltonian is None:
            raise Exception("First you need to add the Hamiltonian!")

        if isinstance(magnetic_entities, dict):
            magnetic_entities = [magnetic_entities]

        out = MagneticEntityList()
        for mag_ent in magnetic_entities:
            out.append(MagneticEntity((self.hamiltonian._dh, self._ds), **mag_ent))

        return out

    def create_pairs(self, pairs: Union[dict, list[dict]]) -> PairList:
        """Creates a list of Pair from a list of dictionaries.

        The dictionaries must contain `ai`, `aj` and `Ruc`, based on the accepted
        input from Pair. If `Ruc` is not given, then it is (0,0,0), by default.
        The Hamiltonian is taken from the instance Hamiltonian.

        Parameters
        ----------
        pairs: Union[dict, list[dict]]
            The list of dictionaries or a single dictionary

        Returns
        -------
        PairList
            List of Pair instances

                    Raise
        -----
        Exception
            Hamiltonian is not added to the instance
        Exception
            Magnetic entities are not added to the instance
        """

        if self.hamiltonian is None:
            raise Exception("First you need to add the Hamiltonian!")

        if len(self.magnetic_entities) == 0:
            raise Exception("First you need to add the magnetic entities!")

        if isinstance(pairs, dict):
            pairs = [pairs]

        out = PairList()
        for pair in pairs:
            ruc = pair.get("Ruc", np.array([0, 0, 0]))
            m1 = self.magnetic_entities[pair["ai"]]
            m2 = self.magnetic_entities[pair["aj"]]
            out.append(Pair(m1, m2, ruc))

        return out

    def add_magnetic_entities(
        self,
        magnetic_entities: Union[
            MagneticEntityList, dict, MagneticEntity, list[dict], list[MagneticEntity]
        ],
    ) -> None:
        """Adds a MagneticEntity or a list of MagneticEntity to the instance.

        It dumps the data to the `magnetic_entities` instance parameter. If a list
        of dictionaries are given, first it tries to convert them to magnetic entities.

        Parameters
        ----------
        magnetic_entities : Union[MagneticEntityList, dict, MagneticEntity, list[Union[dict, MagneticEntity]]]
            Data to add to the instance
        """

        # if it is not a list, then convert
        if not isinstance(magnetic_entities, list) or not MagneticEntityList:
            magnetic_entities = [magnetic_entities]

        # iterate over magnetic entities
        for mag_ent in _tqdm(magnetic_entities, desc="Add magnetic entities"):
            # if it is a MagneticEntity there is nothing to do
            if isinstance(mag_ent, MagneticEntity):
                pass

            # if it is a dictionary
            elif isinstance(mag_ent, dict):
                mag_ent = self.create_magnetic_entities(mag_ent)[0]

            else:
                raise Exception(f"Bad type for MagneticEntity: {type(mag_ent)}")

            # add magnetic entities
            self.magnetic_entities.append(mag_ent)

    def add_pairs(
        self, pairs: Union[PairList, dict, Pair, list[dict], list[Pair]]
    ) -> None:
        """Adds a Pair or a list of Pair to the instance.

        It dumps the data to the ``pairs`` instance parameter. If a list
        of dictionaries are given, first it tries to convert them to pairs.

        Parameters
        ----------
        pairs : Union[PairList, dict, Pair, list[Union[dict, Pair]]]
            Data to add to the instance
        """

        # if it is not a list, then convert
        if not isinstance(pairs, list) or not PairList:
            pairs = [pairs]

        # iterate over pairs
        for pair in _tqdm(pairs, desc="Add pairs"):
            # if it is a Pair there is nothing to do
            if isinstance(pair, Pair):
                pass

            # if it is a dictionary
            elif isinstance(pair, dict):
                pair = self.create_pairs(pair)[0]

            else:
                raise Exception(f"Bad type for Pair: {type(pair)}")

            # add pairs
            self.pairs.append(pair)

    def solve(self, print_memory: bool = False) -> None:
        """Wrapper for Greens function solver.

        The parallelization of the Brillouin sampling can be turned on and
        off. And the parallelization of the energy samples can be tweaked by
        a batch size. CPU and GPU solvers are availabel.

        Parameters
        ----------
        print_memory: bool, optional
            It can be turned on to print extra memory info, by default False
        """

        # reset times
        self.times.restart()

        # check to optimize calculation
        if (self.spin_model == "generalised-grogu") and len(
            self.ref_xcf_orientations
        ) > 3:
            warnings.warn(
                "There are unnecessary orientations for the anisotropy or the exchange solver!"
            )
        elif (self.spin_model == "generalised-fit") and np.array(
            [len(i["vw"]) > 2 for i in self.ref_xcf_orientations]
        ).any():
            warnings.warn(
                "There are unnecessary perpendicular directions for the anisotropy or exchange solver!"
            )

        # check the perpendicularity of directions
        for ref in self.ref_xcf_orientations:
            o = ref["o"]
            vw = ref["vw"]
            perp = np.apply_along_axis(lambda d: np.dot(o, d), 1, vw)
            if not np.allclose(perp, np.zeros_like(perp)):
                raise Exception(f"Not all directions are perpendicular to {o}!")

        # no parallelization
        if self.__parallel_mode is None:
            from .._core.cpu_solvers import default_solver as solver
        # k point parallelization
        elif self.__parallel_mode[0].lower() == "k":
            # choose architecture solver
            if self.__architecture.lower()[0] == "c":  # cpu
                from .._core.cpu_solvers import solve_parallel_over_k as solver
            elif self.__architecture.lower()[0] == "g":  # gpu
                from .._core.gpu_solvers import solve_parallel_over_k as solver
            else:
                raise Exception(f"Unknown architecture: {self.__architecture}")
        else:
            raise Exception(f"Unknown parallelization: {self.__architecture}")

        solver(self, print_memory)
        self.times.measure("solution", restart=True)

    def copy(self):
        """Returns the deepcopy of the instance.

        Returns
        -------
        Hamiltonian
            The copied instance.
        """

        return copy.deepcopy(self)

    def a2M(
        self, atom: Union[int, list[int]], mode: str = "partial"
    ) -> list[MagneticEntity]:
        """Returns the magnetic entities that contains the given atoms.

        The atoms are indexed from the sisl Hamiltonian.

        Parameters
        ----------
        atom : Union[int, list[int]]
            Atomic indices from the sisl Hamiltonian
        mode : {"partial", "complete"}, optional
            Wether to completely or partially match the atoms to the
            magnetic entities, by default "partial"
        Returns
        -------
        list[MagneticEntity]
            List of MagneticEntities that contain the given atoms
        """

        if isinstance(atom, int):
            atom = [atom]

        M: list = []

        # partial matching
        if mode.lower()[0] == "p":
            for at in atom:
                for mag_ent in self.magnetic_entities:
                    if at in mag_ent._atom:
                        M.append(mag_ent)

        # complete matching
        elif mode.lower()[0] == "c":
            for at in atom:
                for mag_ent in self.magnetic_entities:
                    if at == mag_ent._atom:
                        return [mag_ent]

        else:
            raise Exception(f"Unknown mode: {mode}")

        return M


if __name__ == "__main__":
    pass
