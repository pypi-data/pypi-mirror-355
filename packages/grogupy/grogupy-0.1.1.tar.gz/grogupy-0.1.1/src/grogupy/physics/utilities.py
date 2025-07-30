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

import warnings
from typing import Union

import numpy as np
import sisl
from numpy.typing import NDArray


def get_number_of_electrons(dm: Union[str, sisl.DensityMatrix]) -> int:
    """Determines the number of electrons in the system from the density matrix.

    Parameters
    ----------
    dm : Union[str, sisl.DensityMatrix]
        The path to the fdf file or the sisl density matrix

    Returns
    -------
    enum : int
        Number of electrons in the system

    Raises
    ------
    Exception
        Number of electrons could not be determined!
    """

    # get the dm if it is a path
    if isinstance(dm, str):
        dm = sisl.get_sile(dm).read_density_matrix()

    # get the number of electrons from two places
    enum_from_mulliken = dm.mulliken()[0].sum()
    return np.round(enum_from_mulliken).astype(int)


def automatic_emin(infile: str) -> float:
    """It reads the lowest energy level from siesta.

    It uses the .EIG file from siesta that contains the eigenvalues.

    Parameters
    ----------
    infile : str
        The path to the .EIG file or to the .fdf file.

    Returns
    -------
    float
        The energy minimum

    Raises
    ------
    Exception
        Path must point to fdf or EIG file!
    Exception
        Emin could not be determined from infile!
    """

    # define paths from inpath
    if infile.endswith("fdf"):
        fdffile = infile
        eigfile = infile[:-3] + "EIG"
    elif infile.endswith("EIG"):
        fdffile = infile[:-3] + "fdf"
        eigfile = infile
    else:
        raise Exception(f"Path must point to fdf or EIG file: {infile}")

    # try to read the EIG file
    try:
        eigenvalues = sisl.io.siesta.eigSileSiesta(eigfile).read_data()
    # if it is not successful look for the systemlabel in the fdf and try again
    except:
        try:
            with open(fdffile, "r") as file:
                lines = file.readlines()
            for line in lines:
                if line.lower().find("systemlabel") != -1:
                    systemlabel = line.split()[1]
                    break

            eigfile = "/".join(eigfile.split("/")[:-1])
            eigfile += "/" + systemlabel + ".EIG"

            eigenvalues = sisl.io.siesta.eigSileSiesta(eigfile).read_data()

        except:
            raise Exception("Emin could not be determined from ebot and eigfile!")

    return eigenvalues.min()


def blow_up_orbindx(orb_indices: NDArray) -> NDArray:
    """Expand orbital indices to make SPIN BOX indices.

    Parameters
    ----------
        orb_indices: NDArray
            These are the indices in ORBITAL BOX representation

    Returns
    -------
        orb_indices: NDArray
            These are the indices in SPIN BOX representation
    """

    orb_indices = np.array([[2 * o, 2 * o + 1] for o in orb_indices]).flatten()

    return orb_indices


def spin_tracer(M: NDArray) -> dict:
    """Extracts orbital dependent Pauli traces.

    This takes an operator with the orbital-spin sequence:
    orbital 1 up,
    orbital 1 down,
    orbital 2 up,
    orbital 2 down,
    that is in the SPIN-BOX representation,
    and extracts orbital dependent Pauli traces.

    Parameters
    ----------
        M: NDArray
            Traceable matrix in SPIN BOX represenation

    Returns
    -------
        dict
            It contains the traced matrix with "x", "y", "z" and "c", where "c" is the constant part
    """

    M11 = M[0::2, 0::2]
    M12 = M[0::2, 1::2]
    M21 = M[1::2, 0::2]
    M22 = M[1::2, 1::2]

    M_o = dict()
    M_o["x"] = M12 + M21
    M_o["y"] = 1j * (M12 - M21)
    M_o["z"] = M11 - M22
    M_o["c"] = M11 + M22

    return M_o


def parse_magnetic_entity(
    dh: sisl.physics.Hamiltonian,
    atom: Union[None, int, list[int]] = None,
    l: Union[None, int, list[int], list[list[int]]] = None,
    orb: Union[None, int, list[int], list[list[int]]] = None,
) -> tuple[list[int], list[list[int]], list[int], list[str]]:
    """Function to get the orbital indices of a given magnetic entity.

    There are four possible input types:
    1. Cluster: a list of atoms
    2. AtomShell: one atom and a list of shells indexed in the atom or
    a list of atoms and a list of lists containing the shells
    3. AtomOrbital: one atom and a list of orbitals indexed in the atom or
    a list of atoms and a list of lists containing the orbitals
    4. Orbitals: a list of orbitals  indexed in the Hamiltonian

    Parameters
    ----------
        dh: sisl.physics.Hamiltonian
            The Hamiltonian object from ``sisl``
        atom: Union[None, int, list[int]], optional
            Defining atom (or atoms) in the unit cell forming the magnetic entity, by default None
        l: Union[None, int, list[int], list[list[int]]], optional
            Defining the angular momentum channel, by default None
        orb: Union[None, int, list[int], list[list[int]]], optional
            Defining the orbital index in the Hamiltonian or on the atom, by default None

    Returns
    -------
        atom: list[int]
            List of atoms in the magnetic entity
        l: list[list[int]]
            List of angular momentum channels, if unknown, all of them are None
        orbital_indices: list[int]
            The orbital indices of the given magnetic entity indexed by the total Hamiltonian
        tag: list[str]
            The list of tags from the atoms
    """

    # process input and find mode
    # ======================================================================

    # from now on  atom is a list or None
    if isinstance(atom, (int, np.int32, np.int64)):
        atom = [atom]
    if isinstance(atom, np.ndarray):
        atom = atom.tolist()

    # if l is an integer create a list of list as long as the list of atoms,
    # where every list contains integers
    if l is not None:
        if isinstance(l, np.ndarray):
            l = l.tolist()
        if isinstance(l, (int, np.int32, np.int64)):
            l = [[l]] * len(atom)
        if isinstance(l[0], (int, np.int32, np.int64)):
            l = [l] * len(atom)
        if len(l) != len(atom):
            raise Exception("Wrong input: len(l) != len(atom)!")
    # same for orb
    if orb is not None and atom is not None:
        if isinstance(orb, np.ndarray):
            orb = orb.tolist()
        if isinstance(orb, (int, np.int32, np.int64)):
            orb = [[orb]] * len(atom)
        if isinstance(orb[0], (int, np.int32, np.int64)):
            orb = [orb] * len(atom)
        if len(orb) != len(atom):
            raise Exception("Wrong input: len(orb) != len(atom)!")
    elif orb is not None and atom is None:
        if isinstance(orb, np.ndarray):
            orb = orb.tolist()
        if isinstance(orb, (int, np.int32, np.int64)):
            orb = [orb]

    # these are the conditions from the documentation
    if isinstance(atom, list) and l is None and orb is None:
        mode = "Cluster"
    elif isinstance(atom, list) and l is not None and orb is None:
        mode = "AtomShell"
    elif isinstance(atom, list) and l is None and orb is not None:
        mode = "AtomOrbitals"
    elif atom is None and l is None and orb is not None:
        mode = "Orbitals"
    else:
        print("atom:", atom)
        print("l:", l)
        print("orb:", orb)
        raise Exception(
            "Not supported input format. See documentation on what is possible."
        )

    # short name
    geom = dh.geometry
    # from now on  atom is a list or None
    if atom is not None:
        atom = np.array(atom)

    # determine orbital indices based on input
    # ======================================================================

    # the case for the Orbitals keyword, just return the orbitals
    if mode == "Orbitals":
        if isinstance(orb, int):
            orb = [orb]
        orbital_indices = np.array(orb)
    # if it is a Cluster, get all the orbitals from all the atoms
    elif mode == "Cluster":
        orbital_indices = []
        l = []
        for a in atom:
            a_orb_idx = dh.geometry.a2o(a, all=True)
            orbital_indices.append(a_orb_idx)
            l.append([i for i in range(len(dh.atoms[a].orbitals))])
        orbital_indices = np.array(orbital_indices).flatten()

    # if it is an AtomShell it must be a single atom
    # then get the orbitals from that atom that are in
    # the given shells
    elif mode == "AtomShell":
        # container
        orbital_indices = []
        # iterate over atoms
        for i, at in enumerate(atom):
            # first get all the orbitals from the atom
            complete_shell = geom.a2o(at, all=True)

            mask = [orbital.l in l[i] for orbital in geom.atoms[at].orbitals]
            sub_shell = complete_shell[mask]
            if l[i] == [None]:
                sub_shell = complete_shell
                l[i] = list(range(len(geom.atoms[at].orbitals)))

            for o in sub_shell:
                orbital_indices.append(o)

    # if it is an AtomOrbitals it must be a single atom
    # then get given orbitals from that atom
    elif mode == "AtomOrbitals":
        # container
        orbital_indices = []
        # iterate over atoms
        for i, at in enumerate(atom):
            # first get all the orbitals from the atom
            complete_shell = geom.a2o(at, all=True)
            sub_shell = complete_shell[orb[i]]

            try:
                for o in sub_shell:
                    orbital_indices.append(o)
            except:
                orbital_indices.append(sub_shell)

    # convert atom, l and orbitals in the output format
    # ======================================================================
    # in case of Orbitals, reverse find the atoms and
    # atomic orbitals (orb)
    if atom is None:
        atom = []
        orb = []
        for o in orbital_indices:
            # get the atom indices
            at = dh.o2a(o)

            # if there is a new atom create new orb
            # list and append atom
            if len(atom) == 0:
                atom.append(at)
                orb.append([])
            elif at != atom[-1]:
                atom.append(at)
                orb.append([])

            # orbital index on the atom
            o_on_atom = o - dh.atoms.orbitals[: dh.o2a(o)].sum()
            # add the converted orb to the atom orbs
            orb[-1].append(o_on_atom)

    # in case l is not known return a list of None in
    # the shape of atom
    if l is None:
        l = [[None] for _ in atom]

    # determine the tag from the above information
    # ======================================================================
    if mode == "Cluster":
        tag: list[str] = [f"{i}{dh.atoms[i].tag}(l:All)" for i in atom]
    elif mode == "AtomShell":
        tag: list[str] = [
            f"{at}{dh.atoms[at].tag}(l:{'-'.join([str(k) for k in l[i]])})"
            for i, at in enumerate(atom)
        ]
    elif (mode == "AtomOrbitals") or (mode == "Orbitals"):
        tag: list[str] = [
            f"{at}{dh.atoms[at].tag}(o:{'-'.join([str(k) for k in orb[i]])})"
            for i, at in enumerate(atom)
        ]

    return atom, l, orbital_indices, tag


def interaction_energy(
    Vu1_1: NDArray, Vu1_2: NDArray, Gij: NDArray, Gji: NDArray, weights: NDArray
) -> float:
    """The interaction energy variation upon rotations.

    It can be used to calculate the interaction energy
    between two magnetic entities or to calculate some
    of the elements of the anisotropy tensor.

    Parameters
    ----------
    Vu1_1 : NDArray
        First order perturbation of a rotation to one direction
    Vu1_2 : NDArray
        First order perturbation of a rotation to another direction
    Gij : NDArray
        First Green's function slice between the magnetic entities
    Gji : NDArray
        Second Green's function slice between the magnetic entities
    weights : NDArray
        The weights from the energy contour integral

    Returns
    -------
    float
        The interaction energy variation
    """

    # The Szunyogh-Lichtenstein formula
    traced: NDArray = np.trace(
        (Vu1_1 @ Gij @ Vu1_2 @ Gji), axis1=1, axis2=2
    )  # this is the on site projection
    # evaluation of the contour integral
    if len(traced) == 1:
        warnings.warn(
            "Only one energy point is given for integration! Returning energy point instead!"
        )
        return float(-1 / np.pi * np.imag(traced * weights).squeeze())

    integral = float(-1 / np.pi * np.sum(np.imag(traced * weights)).squeeze())
    return integral


def second_order_energy(
    Vu1: NDArray, Vu2: NDArray, Gii: NDArray, weights: NDArray
) -> float:
    """The second order energy variation upon rotations.

    Parameters
    ----------
    Vu1 : NDArray
        First order perturbation of a rotation
    Vu2 : NDArray
        Second order perturbation of a rotation
    Gii : NDArray
        Green's function slice
    weights : NDArray
        The weights from the energy contour integral

    Returns
    -------
    float
        The second order energy variation
    """

    # The Szunyogh-Lichtenstein formula
    traced: NDArray = np.trace(
        (Vu2 @ Gii + 0.5 * Vu1 @ Gii @ Vu1 @ Gii), axis1=1, axis2=2
    )  # this is the on site projection
    # evaluation of the contour integral
    if len(traced) == 1:
        warnings.warn(
            "Only one energy point is given for integration! Returning energy point instead!"
        )
        return float(-1 / np.pi * np.imag(traced * weights).squeeze())

    integral = float(-1 / np.pi * np.sum(np.imag(traced * weights)).squeeze())
    return integral


def calculate_anisotropy_tensor(energies: NDArray) -> tuple[NDArray, float]:
    """Calculates the renormalized anisotropy tensor from the energies.

    The energies must be in the shape of a 3 by 3 matrix, where each row is
    an orientation and each column is a second order perpendicular rotation.

    Parameters
    ----------
        energies : NDArray
            The energies of the rotations

    Returns
    -------
        K : NDArray
            Elements of the anisotropy tensor
        consistency_check : float
            Absolute value of the difference from the consistency check
    """

    # more directions are useless
    if len(energies) > 3:
        warnings.warn(
            "There are more exchange field reference directions given, than what is needed.\nOnly the first three is used!"
        )

    K = np.zeros((3, 3))

    # WARNING this has been rewritten to work with the auto-generated directions, meaning
    # the orientations are:
    # o=[1, 0, 0], vw=[[0, 0, -1], [0, 1, 0]]
    # o=[0, 1, 0], vw=[[1, 0, 0], [0, 0, -1]],
    # o=[0, 0, 1], vw=[[1, 0, 0], [0, 1, 0]],

    # WARNING O should be Z, but it is not if we index incorrectly
    # the energies are given like
    # E**2({o},v), E({o},vw), E({o},wv), E**2({o},w), E**2({o},(v+w)/sqrt(2))
    # E**2({v},o), E({v},ow), E({v},wo), E**2({v},w), E**2({v},(o+w)/sqrt(2))
    # E**2({w},o), E({w},ov), E({w},vo), E**2({w},v), E**2({w},(v+o)/sqrt(2))

    # calculate the diagonal tensor elements
    # Koo = E**2({v},w) - E**2({v},o)
    K[0, 0] = energies[1, 3] - energies[1, 0]
    # Kvv = E**2({o},w) - E**2({o},v)
    K[1, 1] = energies[0, 0] - energies[0, 3]
    K[2, 2] = 0

    # calculate the off-diagonal tensor elements
    # Kvw = 1/2 * (E**2({o},v) + E**2({o},w)) - E**2({o},(v+w)/sqrt(2))
    K[0, 1] = (energies[2, 0] + energies[2, 3]) / 2 - energies[2, 4]
    K[1, 0] = K[0, 1]
    K[0, 2] = -(energies[1, 0] + energies[1, 3]) / 2 + energies[1, 4]
    K[2, 0] = K[0, 2]
    K[1, 2] = -(energies[0, 0] + energies[0, 3]) / 2 + energies[0, 4]
    K[2, 1] = K[1, 2]

    # perform consistency check
    calculated_diff = K[1, 1] - K[0, 0]
    expected_diff = energies[2, 0] - energies[2, 3]
    consistency_check = abs(calculated_diff - expected_diff)

    return K, consistency_check


def fit_anisotropy_tensor(energies: NDArray, ref_xcf: list[dict]) -> NDArray:
    """Fits the anisotropy tensor to the energies.

    It uses a fitting method to calculate the anisotropy tensor from the
    reference directions and its different representations.

    Parameters
    ----------
    energies : NDArray
        Energies upon rotations
    ref_xcf : list[dict]
        The reference directions containing the orientation and perpendicular directions

    Returns
    -------
        K : NDArray
            Elements of the anisotropy tensor
    """

    warnings.warn("This is experimenal!")

    A = np.zeros((5, 5))
    cA = np.zeros(5)

    for i in range(len(ref_xcf)):
        E = energies[i, :4]
        v = ref_xcf[i]["vw"][0]
        w = ref_xcf[i]["vw"][1]

        vw = np.array(
            [
                np.outer(w, w) - np.outer(v, v),
                np.outer(v, w),
                np.outer(w, v),
                np.outer(v, v) - np.outer(w, w),
            ]
        )
        c = np.array([E[0] - E[3], E[1], E[2], E[3] - E[0]])

        for ci, vwi in zip(c, vw):
            a = np.array(
                [
                    vwi[0, 0],
                    -2 * (vwi[0, 1] + vwi[1, 0]),  # HERE is the -2
                    -2 * (vwi[0, 2] + vwi[2, 0]),  # HERE is the -2
                    vwi[1, 1],
                    -2 * (vwi[1, 2] + vwi[2, 1]),  # HERE is the -2
                ]
            )

            A += np.outer(a, a)
            cA += ci * a

    K = np.linalg.inv(A) @ cA
    out = np.array(
        [
            [K[0], K[1], K[2]],
            [K[1], K[3], K[4]],
            [K[2], K[4], 0],
        ]
    )

    return out


def calculate_exchange_tensor(
    energies: NDArray,
) -> tuple[float, NDArray, NDArray, NDArray]:
    """Calculates the exchange tensor from the energies.

    It produces the isotropic exchange, the relevant elements
    from the Dzyaloshinskii-Morilla (Dm) tensor, the symmetric-anisotropy
    and the complete exchange tensor.

    Parameters
    ----------
        energies: NDArray
            Energies upon rotations

    Returns
    -------
        J_iso: float
            Isotropic exchange (Tr[J] / 3)
        J_S: NDArray
            Symmetric-anisotropy (J_S = J - J_iso * I --> Jxx, Jyy, Jxy, Jxz, Jyz)
        D: NDArray
            DM elements (Dx, Dy, Dz)
        J: NDArray
            Complete exchange tensor flattened (Jxx, Jxy, Jxz, Jyx, Jyy, Jyz, Jzx, Jzy, Jzz)
    """

    # more directions are useless
    if len(energies) > 3:
        warnings.warn(
            "There are more exchange field reference directions given, than what is needed.\nOnly the first three is used!"
        )

    # Initialize output arrays
    J_diag = np.zeros(3)
    J_S = np.zeros(3)
    D = np.zeros(3)
    J = np.zeros((3, 3))

    # first calculate the diagonal elements
    J_diag[0] = energies[1, 3]
    J_diag[1] = energies[2, 0]
    J_diag[2] = energies[0, 3]

    # symmetric part
    J_S[0] = 0.5 * (energies[0, 1] + energies[0, 2])
    J_S[1] = 0.5 * (energies[1, 1] + energies[1, 2])
    J_S[2] = -0.5 * (energies[2, 1] + energies[2, 2])

    # anti-symmetric part
    D[0] = 0.5 * (energies[0, 1] - energies[0, 2])
    D[1] = 0.5 * (energies[1, 1] - energies[1, 2])
    D[2] = 0.5 * (energies[2, 1] - energies[2, 2])

    # put together
    J[0, 0] = J_diag[0]
    J[1, 1] = J_diag[1]
    J[2, 2] = J_diag[2]
    J[0, 1] = J_S[2] + D[2]
    J[0, 2] = J_S[1] - D[1]
    J[1, 2] = J_S[0] + D[0]
    J[1, 0] = J_S[2] - D[2]
    J[2, 0] = J_S[1] + D[1]
    J[2, 1] = J_S[0] - D[0]

    J_iso = np.trace(J) / 3

    return J_iso, J_S, D, J


def fit_exchange_tensor(
    energies: NDArray, ref_xcf: list[dict]
) -> tuple[float, NDArray, NDArray, NDArray]:
    """Fits the exchange tensor to the energies.

    It uses a fitting method to calculate the exchange tensor from the
    reference directions and its different representations.

    Parameters
    ----------
    energies : NDArray
        Energies upon rotations
    ref_xcf : list[dict]
        The reference directions containing the orientation and perpendicular directions

    Returns
    -------
        J_iso : float
            Isotropic exchange (Tr[J] / 3)
        J_S : NDArray
            Symmetric-anisotropy (J_S = J - J_iso * I -> Jxx, Jyy, Jxy, Jxz, Jyz)
        D : NDArray
            DM elements (Dx, Dy, Dz)
        J : NDArray
            Complete exchange tensor flattened (Jxx, Jxy, Jxz, Jyx, Jyy, Jyz, Jzx, Jzy, Jzz)
    """

    warnings.warn("This is experimenal!")

    # Based on the BME consultation
    M = np.zeros((9, 9))
    V = np.zeros(9)

    for i in range(len(ref_xcf)):
        E = energies[i, :4]
        e1 = ref_xcf[i]["vw"][0]
        e2 = ref_xcf[i]["vw"][1]
        e = ref_xcf[i]["o"]

        e_primes = np.array([[e1, e1], [e2, e1], [e1, e2], [e2, e2]])

        for j in range(len(e_primes)):
            epl = np.cross(e, e_primes[j, 0])
            epr = np.cross(e, e_primes[j, 1])
            epsilon1 = np.outer(epl, epr).flatten()
            epsilon2 = np.outer(epr, epl).flatten()
            M += np.outer(epsilon1, epsilon2)
            V += E[j] * epsilon1

    J = np.linalg.solve(M, V)

    # dump data to instance
    J = J.reshape(3, 3)
    J_S = 0.5 * (J + J.T)
    D = 0.5 * (J - J.T)

    J_iso = np.trace(J) / 3

    J_S = np.array([J_S[1, 2], J_S[0, 2], J_S[0, 1]])
    D = np.array([D[1, 2], -D[0, 2], D[0, 1]])

    return J_iso, J_S, D, J


def calculate_isotropic_only(
    energies: NDArray,
) -> float:
    """Calculates the isotropic exchange only.

    Parameters
    ----------
        energies: NDArray
            Energy upon one single rotation

    Returns
    -------
        J_iso: float
            Isotropic exchange interaction
    """

    # the isotropic exchange
    J_iso = energies[0, 0]

    return J_iso


if __name__ == "__main__":
    pass
