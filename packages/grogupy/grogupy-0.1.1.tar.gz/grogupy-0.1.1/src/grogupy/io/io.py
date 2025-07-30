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

import importlib.util
import pickle
import warnings
from os.path import join
from typing import Union

import numpy as np

from grogupy import __version__
from grogupy.batch.timing import DefaultTimer
from grogupy.physics import Builder, Contour, Hamiltonian, Kspace, MagneticEntity, Pair

from .utilities import strip_dict_structure


def load_DefaultTimer(infile: Union[str, dict]) -> DefaultTimer:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    DefaultTimer
        The DefaultTimer instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(DefaultTimer)
    out.__setstate__(infile)

    return out


def load_Contour(infile: Union[str, dict]) -> Contour:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Contour
        The Contour instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(Contour)
    out.__setstate__(infile)

    return out


def load_Kspace(infile: Union[str, dict]) -> Kspace:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Kspace
        The Kspace instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(Kspace)
    out.__setstate__(infile)

    return out


def load_MagneticEntity(infile: Union[str, dict]) -> MagneticEntity:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    MagneticEntity
        The MagneticEntity instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(MagneticEntity)
    out.__setstate__(infile)

    return out


def load_Pair(infile: Union[str, dict]) -> Pair:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Pair
        The Pair instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(Pair)
    out.__setstate__(infile)

    return out


def load_Hamiltonian(infile: Union[str, dict]) -> Hamiltonian:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Hamiltonian
        The Hamiltonian instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(Hamiltonian)
    out.__setstate__(infile)

    return out


def load_Builder(infile: Union[str, dict]) -> Builder:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Builder
        The Builder instance that was loaded
    """

    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            infile = pickle.load(file)

    # build instance
    out = object.__new__(Builder)
    out.__setstate__(infile)

    return out


def load(
    infile: Union[str, dict]
) -> Union[DefaultTimer, Contour, Kspace, MagneticEntity, Pair, Hamiltonian, Builder]:
    """Recreates the instance from a pickled state.

    Parameters
    ----------
    infile : Union[str, dict]
        Either the path to the file or the appropriate
        dictionary for the setup

    Returns
    -------
    Union[DefaultTimer, Contour, Kspace, MagneticEntity, Pair, Hamiltonian, Builder]
        The instance that was loaded
    """
    # load pickled file
    if isinstance(infile, str):
        if not infile.endswith(".pkl"):
            infile += ".pkl"
        with open(infile, "rb") as file:
            dat = pickle.load(file)
    else:
        dat = infile

    if list(dat.keys()) == [
        "times",
        "kspace",
        "contour",
        "hamiltonian",
        "magnetic_entities",
        "pairs",
        "_Builder__low_memory_mode",
        "_Builder__greens_function_solver",
        "_Builder__max_g_per_loop",
        "_Builder__parallel_mode",
        "_Builder__architecture",
        "_Builder__apply_spin_model",
        "_Builder__spin_model",
        "ref_xcf_orientations",
        "_rotated_hamiltonians",
        "SLURM_ID",
        "_Builder__version",
    ]:
        return load_Builder(infile)

    elif list(dat.keys()) == [
        "times",
        "kspace",
        "contour",
        "hamiltonian",
        "magnetic_entities",
        "pairs",
        "ref_xcf_orientations",
        "_rotated_hamiltonians",
        "SLURM_ID",
        "_Builder__version",
    ]:
        b = load_Builder(infile)
        warnings.warn(
            f"There is a mismatch between Builder ({b.version}) and current ({__version__}) version!"
        )
        return b

    elif list(dat.keys()) == [
        "times",
        "_dh",
        "_ds",
        "infile",
        "_spin_state",
        "H",
        "S",
        "scf_xcf_orientation",
        "orientation",
        "_Hamiltonian__no",
        "_Hamiltonian__cell",
        "_Hamiltonian__sc_off",
        "_Hamiltonian__uc_in_sc_index",
    ]:
        return load_Hamiltonian(infile)
    elif list(dat.keys()) == [
        "_dh",
        "M1",
        "M2",
        "supercell_shift",
        "_Gij",
        "_Gji",
        "energies",
        "J_iso",
        "J",
        "J_S",
        "D",
        "_Pair__SBS1",
        "_Pair__SBS2",
        "_Pair__SBI1",
        "_Pair__SBI2",
        "_Pair__tags",
        "_Pair__cell",
        "_Pair__supercell_shift_xyz",
        "_Pair__xyz",
        "_Pair__xyz_center",
        "_Pair__distance",
        "_Pair__energies_meV",
        "_Pair__energies_mRy",
        "_Pair__J_meV",
        "_Pair__J_mRy",
        "_Pair__D_meV",
        "_Pair__D_mRy",
        "_Pair__J_S_meV",
        "_Pair__J_S_mRy",
        "_Pair__J_iso_meV",
        "_Pair__J_iso_mRy",
    ]:
        return load_Pair(infile)
    elif list(dat.keys()) == [
        "_dh",
        "_ds",
        "infile",
        "_atom",
        "_l",
        "_orbital_box_indices",
        "_tags",
        "_total_mulliken",
        "_local_mulliken",
        "_spin_box_indices",
        "_xyz",
        "_Vu1",
        "_Vu2",
        "_Gii",
        "energies",
        "K",
        "K_consistency",
        "_MagneticEntity__tag",
        "_MagneticEntity__SBS",
        "_MagneticEntity__xyz_center",
        "_MagneticEntity__total_Q",
        "_MagneticEntity__total_S",
        "_MagneticEntity__total_Sx",
        "_MagneticEntity__total_Sy",
        "_MagneticEntity__total_Sz",
        "_MagneticEntity__local_Q",
        "_MagneticEntity__local_S",
        "_MagneticEntity__local_Sx",
        "_MagneticEntity__local_Sy",
        "_MagneticEntity__local_Sz",
        "_MagneticEntity__energies_meV",
        "_MagneticEntity__energies_mRy",
        "_MagneticEntity__K_meV",
        "_MagneticEntity__K_mRy",
        "_MagneticEntity__K_consistency_meV",
        "_MagneticEntity__K_consistency_mRy",
    ]:
        return load_MagneticEntity(infile)
    elif list(dat.keys()) == ["times", "_Kspace__kset", "kpoints", "weights"]:
        return load_Kspace(infile)
    elif list(dat.keys()) == [
        "times",
        "_Contour__automatic_emin",
        "_eigfile",
        "_emin",
        "_emax",
        "_eset",
        "_esetp",
        "samples",
        "weights",
    ]:
        return load_Contour(infile)
    elif list(dat.keys()) == ["_DefaultTimer__start_measure", "_times"]:
        return load_DefaultTimer(infile)
    else:
        raise Exception("Unknown pickle format!")


def save(
    object: Union[
        DefaultTimer, Contour, Kspace, MagneticEntity, Pair, Hamiltonian, Builder
    ],
    path: str,
    compress: int = 2,
) -> None:
    """Saves the instance from a pickled state.

    The compression level can be set to 0,1,2,3. Every other value defaults to 3.

    0. This means that there is no compression at all.

    1. This means, that the keys "_dh" and "_ds" are set
       to None, because othervise the loading would be dependent
       on the sisl version

    2. This contains compression 1, but sets the keys "Gii",
       "Gij", "Gji", "Vu1" and "Vu2" to [], to save space

    Parameters
    ----------
    object : Union[DefaultTimer, Contour, Kspace, MagneticEntity, Pair, Hamiltonian, Builder]
        Object from the grogupy library
    path: str
        The path to the output file
    compress: int, optional
        The level of lossy compression of the output pickle, by default 3
    """

    # check if the object is ours
    if object.__module__.split(".")[0] == "grogupy":
        # add pkl so we know it is pickled
        if not path.endswith(".pkl"):
            path += ".pkl"

        # the dictionary to be saved
        out_dict = object.__getstate__()

        # remove large objects to save memory or to avoid sisl loading errors
        if compress == 0:
            pass
        elif compress == 1:
            out_dict = strip_dict_structure(out_dict, pops=["_dh", "_ds"], setto=None)
        # compress 2 is the default
        else:
            out_dict = strip_dict_structure(out_dict, pops=["_dh", "_ds"], setto=None)
            out_dict = strip_dict_structure(
                out_dict,
                pops=[
                    "_Gii",
                    "_Gij",
                    "_Gji",
                    "_Vu1",
                    "_Vu2",
                ],
                setto=[],
            )

        # write to file
        with open(path, "wb") as f:
            pickle.dump(out_dict, f)

    else:
        raise Exception(
            f"The object is from package {object.__module__.split('.')[0]} instead of grogupy!"
        )


def save_UppASD(
    builder: Builder,
    folder: str,
    fast_compare: bool = False,
    magnetic_moment: str = "total",
    comments: bool = True,
):
    """Writes the UppASD input files to the given folder.

    The created input files are the posfile, momfile and
    jfile. Furthermore a cell.tmp.txt file is created which
    contains the unit cell for easy copy pasting.

    Parameters
    ----------
    builder : Builder
        Main simulation object containing all the data
    folder : str
        The out put folder where the files are created
    fast_compare: bool, optional
        When determining the magnetic entity index a fast comparison can
        be used where only the tags are checked, by default False
    magnetic_moment: str, optional
        It switches the used spin moment in the output, can be 'total'
        for the whole atom or atoms involved in the magnetic entity or
        'local' if we only use the part of the mulliken projections that
        are exactly on the magnetic entity, which may be just a subshell
        of the atom, by default 'total'
    comments: bool, optional
        Wether to add comments in the beginning of the cell.tmp.txt, by default True

    """

    if builder.apply_spin_model == False:
        raise Exception(
            "Exchange and anisotropy is not calculated! Use apply_spin_model=True"
        )

    posfile = ""
    momfile = ""
    if not builder.spin_model == "isotropic-only":
        # iterating over magnetic entities
        for i, mag_ent in enumerate(builder.magnetic_entities):
            # calculating positions in basis vector coordinates
            basis_vector_coords = mag_ent.xyz_center @ np.linalg.inv(
                builder.hamiltonian.cell
            )
            bvc = np.around(basis_vector_coords, decimals=5)
            # adding line to posfile
            posfile += f"{i+1} {i+1} {bvc[0]:.5f} {bvc[1]:.5f} {bvc[2]:.5f}\n"
            # if magnetic moment is local
            if magnetic_moment.lower() == "l":
                S = np.array([mag_ent.local_Sx, mag_ent.local_Sy, mag_ent.local_Sz])
            # if magnetic moment is total
            else:
                S = np.array([mag_ent.total_Sx, mag_ent.total_Sy, mag_ent.total_Sz])
            # get the norm of the vector
            S_abs = np.linalg.norm(S)
            S = S / S_abs
            S = np.around(S, decimals=5)
            S_abs = np.around(S_abs, decimals=5)
            # adding line to momfile
            momfile += f"{i+1} 1 {S_abs:.5f} {S[0]:.5f} {S[1]:.5f} {S[2]:.5f}\n"
    else:
        momfile = "No on site anisotropy in Isotropic Exchange only mode!"

    jfile = ""
    if not builder.spin_model == "isotropic-only":
        # adding anisotropy to jfile
        for i, mag_ent in enumerate(builder.magnetic_entities):
            K = np.around(mag_ent.K_mRy.flatten(), decimals=5)
            # adding line to jfile
            jfile += (
                f"{i+1} {i+1} 0 0 0 " + " ".join(map(lambda x: f"{x:.5f}", K)) + "\n"
            )

    # iterating over pairs
    for pair in builder.pairs:
        # iterating over magnetic entities and comparing them to the ones stored in the pairs
        for i, mag_ent in enumerate(builder.magnetic_entities):
            if fast_compare:
                if mag_ent.tag == pair.M1.tag:
                    ai = i + 1
                if mag_ent.tag == pair.M2.tag:
                    aj = i + 1
            else:
                if mag_ent == pair.M1:
                    ai = i + 1
                if mag_ent == pair.M2:
                    aj = i + 1

        # this is the unit cell shift
        shift = pair.supercell_shift
        if builder.spin_model == "isotropic-only":
            J = np.around(-2 * pair.J_iso_mRy.flatten(), decimals=5)
        else:
            # -2 for convention, from Marci
            J = np.around(-2 * pair.J_mRy.flatten(), decimals=5)
        # adding line to jfile
        jfile += (
            f"{ai} {aj} {shift[0]} {shift[1]} {shift[2]} "
            + " ".join(map(lambda x: f"{x:.5f}", J))
            + "\n"
        )

    # cell as easily copy pastable string
    c = np.around(builder.hamiltonian.cell, 5)
    string = f"{c[0,0]} {c[0,1]} {c[0,2]}\n{c[1,0]} {c[1,1]} {c[1,2]}\n{c[2,0]} {c[2,1]} {c[2,2]}\n\n\n"

    # writing them to the given folder
    with open(join(folder, "cell.tmp.txt"), "w") as f:
        print(string, file=f)

        # if comments are requested
        if comments:
            print(
                "\n".join(["# " + row for row in builder.__str__().split("\n")]), file=f
            )

    with open(join(folder, "jfile"), "w") as f:
        print(jfile, file=f)
    with open(join(folder, "momfile"), "w") as f:
        print(momfile, file=f)
    with open(join(folder, "posfile"), "w") as f:
        print(posfile, file=f)


def save_magnopy(
    builder: Builder,
    path: str,
    magnetic_moment: str = "total",
    precision: Union[None, int] = None,
    comments: bool = True,
) -> None:
    """Creates a magnopy input file based on a path.

    It does not create the folder structure if the path is invalid.
    It saves to the outfile.

    Parameters
    ----------
    builder: Builder
        The system that we want to save
    path: str
        Output path
    magnetic_moment: str, optional
        It switches the used magnetic moment in the output, can be 'total'
        for the whole atom or atoms involved in the magnetic entity or
        'local' if we only use the part of the mulliken projections that
        are exactly on the magnetic entity, which may be just a subshell
        of the atom, by default 'total'
    precision: Union[None, int], optional
        The precision of the magnetic parameters in the output, if None
        everything is written, by default None
    comments: bool, optional
        Wether to add comments in the beginning of file, by default True
    """

    if not path.endswith(".magnopy.txt"):
        path += ".magnopy.txt"

    data = builder.to_magnopy(
        magnetic_moment=magnetic_moment, precision=precision, comments=comments
    )
    with open(path, "w") as file:
        file.write(data)


def read_magnopy(file: str, dense_output: bool = True):
    """This function reads the magnopy input file and returns a dictionary

    Parameters
    ----------
    file: str
        Path to the ``magnopy`` input file
    dense_output: bool, optional
        It adds the magnetic sites to the anisotropy and then the anisotropy
        to the pair information for easier post processing, by duplicating
        data, by default True

    Returns
    -------
    dict
        The dictionary containing all the information from the ``magnopy`` file

    Exception
    ---------
        If there is an unrecognised section
    """

    # read file
    with open(file, "r") as f:
        lines = f.readlines()

    # this is a dense line that splits the magnopy file to sections,
    # then splits the sections by lines
    # this creates a list if lists of strings
    sections = [
        sec.split("\n")
        for sec in "".join(lines).split(
            "================================================================================\n"
        )[1:-1]
    ]

    out = dict()
    # iterate over sections
    for section in sections:
        if section[0] == "GROGU INFORMATION":
            out["grogu_information"] = "\n".join(section)
        elif section[0] == "Magnetic sites":
            if section[2] == "Name x (Ang) y (Ang) z (Ang) s sx sy sz":
                magnetic_sites = []
                for l in section[3:-1]:
                    l = l.split()
                    site = dict()
                    site["tag"] = l[0]
                    site["xyz"] = [
                        float(l[1]),
                        float(l[2]),
                        float(l[3]),
                    ]
                    site["s"] = float(l[4])
                    site["s_xyz"] = [
                        float(l[5]),
                        float(l[6]),
                        float(l[7]),
                    ]
                    magnetic_sites.append(site)
                out["magnetic_sites"] = magnetic_sites
            else:
                warnings.warn("Not standard magnetic site definition!")
                out["magnetic_sites"] = section
        elif section[0] == "Hamiltonian convention":
            hamiltonian_convention = []
            for l in section[1:-1]:
                l = l.split()
                convention = dict()
                convention["_".join(l[:-1]).lower()] = l[-1]
                hamiltonian_convention.append(convention)
            out["hamiltonian_convention"] = hamiltonian_convention
        elif section[0] == "Cell (Ang)":
            out["cell"] = np.array(
                [
                    section[1].split(),
                    section[2].split(),
                    section[3].split(),
                ]
            ).astype(float)
        elif section[0] == "Intra-atomic anisotropy tensor (meV)":
            # similar to the above processing, but here we separate
            # the intra-atomic anisotropies to subsections
            tmp = "\n".join(section).split(
                "--------------------------------------------------------------------------------\n"
            )
            magnetic_sites = []
            for site in tmp[1:-1]:
                site = site.split("\n")[:-1]
                out_site = dict()
                out_site["tag"] = site[0]
                out_site["K"] = np.array(
                    [
                        site[2].split(),
                        site[3].split(),
                        site[4].split(),
                    ]
                ).astype(float)
                magnetic_sites.append(out_site)
            out["anisotropy"] = magnetic_sites
        elif section[0] == "Exchange tensor (meV)":
            # similar to the above processing, but here we separate
            # the pairs to subsections
            tmp = "\n".join(section).split(
                "--------------------------------------------------------------------------------\n"
            )
            pairs = []
            for pair in tmp[2:-1]:
                pair = pair.split("\n")[:-1]
                out_pair = dict()
                info_line = pair[0].split()
                out_pair["tags"] = np.array(
                    [
                        info_line[0],
                        info_line[1],
                    ]
                )
                out_pair["cell_shift"] = np.array(
                    [
                        info_line[2],
                        info_line[3],
                        info_line[4],
                    ]
                ).astype(int)
                out_pair["distance"] = float(info_line[5])
                out_pair["J"] = np.array(
                    [
                        pair[2].split(),
                        pair[3].split(),
                        pair[4].split(),
                    ]
                ).astype(float)
                pairs.append(out_pair)
            out["exchange"] = pairs
        else:
            raise Exception(f"Unknown section title: {section[0]}")

    if dense_output:
        for ani in out["anisotropy"]:
            for site in out["magnetic_sites"]:
                if ani["tag"] == site["tag"]:
                    ani["xyz"] = site["xyz"]
                    ani["s"] = site["s"]
                    ani["s_xyz"] = site["s_xyz"]
        for pair in out["exchange"]:
            for site in out["anisotropy"]:
                if pair["tags"][0] == site["tag"]:
                    pair["ai"] = site
                if pair["tags"][1] == site["tag"]:
                    pair["aj"] = site
    return out


def read_fdf(path: str) -> dict:
    """It reads the simulation parameters, magnetic entities and pairs from an fdf file.

    Parameters
    ----------
        path: str
            The path to the .fdf file

    Returns
    -------
        out: dict
            The input parameters
    """

    out = dict()
    with open(path) as f:
        while True:
            # preprocess
            line = f.readline()
            if not line:
                break
            line = line[: line.find("#")]
            if len(line.strip()) != 0:
                line = line.split()
                line[0] = line[0].replace("_", "").replace(".", "").lower()

                # these are blocks
                if line[0].lower() == r"%block":
                    # name so we can choose process function
                    name = line[1].replace("_", "").replace(".", "").lower()

                    # iterate over lines and get preprocessed data
                    lines = []
                    while True:
                        # preprocess
                        line = f.readline()
                        # if endblock break loop
                        if line.split()[0].lower() == r"%endblock":
                            break
                        if not line:
                            raise Exception(f"End of file in block: {name}")
                        line = line[: line.find("#")]
                        if len(line.strip()) != 0:
                            lines.append(line)

                    if name == "refxcforientations":
                        out_lines = []
                        for l in lines:
                            l = l.split()
                            # we expected either 3 numbers of reference direction or
                            # some number of perpendicular directions which is defined
                            # by 3 numbers as well
                            if len(l) % 3 != 0:
                                raise Exception(
                                    "Some number of 3D vectors are expected."
                                )
                            # check if the row is integer or not
                            just_int = True
                            for v in l:
                                if not v.isdigit():
                                    just_int = False
                            # if the perpendicular directions are not given
                            if len(l) == 3:
                                if just_int:
                                    out_lines.append(list(map(int, l)))
                                else:
                                    out_lines.append(list(map(float, l)))
                            # if it is an input dictionary format
                            else:
                                if just_int:
                                    l = list(map(int, l))
                                else:
                                    l = list(map(float, l))
                                out_ref = {"o": [], "vw": []}
                                # iterate over the vectors
                                for i in range(len(l) // 3):
                                    if i == 0:
                                        out_ref["o"] = l[i * 3 : i * 3 + 3]
                                    else:
                                        out_ref["vw"].append(l[i * 3 : i * 3 + 3])
                                out_lines.append(out_ref)

                    elif name == "magneticentities":
                        out_lines = []
                        for l in lines:
                            l = l.split()
                            if l[0].lower() == "orbitals":
                                out_lines.append(dict(orb=list(map(int, l[1:]))))
                            elif l[0].lower() == "cluster":
                                out_lines.append(dict(atom=list(map(int, l[1:]))))
                            elif l[0].lower() == "atom":
                                if len(l) != 2:
                                    raise Exception("Atom should be a single atom!")
                                else:
                                    out_lines.append(dict(atom=int(l[1])))
                            elif l[0].lower() == "atomshell":
                                out_lines.append(
                                    dict(atom=int(l[1]), l=list(map(int, l[2:])))
                                )
                            elif l[0].lower() == "atomorbital":
                                out_lines.append(
                                    dict(atom=int(l[1]), orb=list(map(int, l[2:])))
                                )
                            else:
                                raise Exception("Unknown magnetic entity!")

                    elif name == "pairs":
                        out_lines = []
                        for l in lines:
                            l = l.split()
                            out_lines.append(
                                dict(
                                    ai=int(l[0]),
                                    aj=int(l[1]),
                                    Ruc=list(map(int, l[2:5])),
                                )
                            )
                            # this is special, because we have to set up a dict from a single line
                    elif name == "kwargsformagent":
                        out_lines = dict()
                        for l in lines:
                            l = l.split()
                            if l[0].lower() == "l":
                                out_lines["l"] = list(map(int, l[1:]))
                            elif l[0].lower() == "o":
                                out_lines["orb"] = list(map(int, l[1:]))
                            else:
                                if l[1].lower() == "l":
                                    out_lines[l[0]]["l"] = list(map(int, l[2:]))
                                elif l[1].lower() == "o":
                                    out_lines[l[0]]["orb"] = list(map(int, l[2:]))
                                else:
                                    raise Exception(
                                        f"Unknown kwarg for magnetic entities: {l[0]}!"
                                    )
                    else:
                        pass
                    out[name] = out_lines

                # these are single line lists
                elif len(line) > 2:
                    just_int = True
                    for l in line[1:]:
                        if not l.isdigit():
                            just_int = False
                    if just_int:
                        out[line[0]] = list(map(int, line[1:]))
                    else:
                        out[line[0]] = list(map(float, line[1:]))

                # one keyword stuff
                elif len(line) == 2:
                    # check for integers
                    if line[1].isdigit():
                        out[line[0]] = int(line[1])
                    else:
                        # else try floats and continue if it works
                        try:
                            out[line[0]] = float(line[1])
                            continue
                        except:
                            pass
                        # the rest are strings, none or bool
                        if line[1].lower() == "none":
                            out[line[0]] = None
                        elif line[1].lower() == "true":
                            out[line[0]] = True
                        elif line[1].lower() == "false":
                            out[line[0]] = False
                        else:
                            out[line[0]] = line[1]
    return out


def read_py(path: str) -> dict:
    """Reading input parameters from a .py file.

    Parameters
    ----------
    path: str
        The path to the input file

    Returns
    -------
    out : dict
        The input parameters
    """

    # Create the spec
    spec = importlib.util.spec_from_file_location("grogupy_command_line_input", path)

    # Create the module
    if spec is not None:
        params = importlib.util.module_from_spec(spec)
        loader = spec.loader
        if loader is not None:
            loader.exec_module(params)
        else:
            raise Exception("File could not be loaded!")

    else:
        raise Exception("File could not be loaded!")

    # convert to dictionary
    out = dict()
    for name in params.__dir__():
        if not name.startswith("__") or name == "np" or name == "numpy":
            n = name.replace("_", "").replace(".", "").lower()
            out[n] = params.__dict__[name]

    return out


if __name__ == "__main__":
    pass
