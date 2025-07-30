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

import re
import warnings
from typing import Any, Union

import numpy as np
import sisl


def decipher(
    tag: str,
) -> tuple[list[int], Union[None, list[int]], Union[None, list[int]]]:
    """Gets the ``atom``, ``l`` and ``orb`` from the tag of the magnetic entity.

    Parameters
    ----------
    tag : str
        The tag of the magnetic entity that we want to decipher

    Returns
    -------
    atom : list[int]
        The atoms from the tag
    l : Union[None, list[int]]
        The shells from the tag
    orb : Union[None, list[int]]]
        The orbitals from the tag

    Raises
    ------
    Exception
        The tag was not created by the conventional format
    """

    # split the magnetic entity if it consists of multiple atoms
    tags: list[str] = tag.split("--")
    # some default values
    atom_index = []
    l = []
    orb = []
    # iterate over atoms
    for tag in tags:
        # this is the atom tag
        atom_index.append(int(re.findall(r"\d+", tag.split("(")[0])[0]))
        # this is o for orbital and l for shell
        mode = tag.split("(")[1].split(")")[0][0]
        # the exact numbers that define the mode
        info = tag.split("(")[1].split(")")[0][2:].split("-")

        # shell mode
        if mode.lower() == "l":
            # if the all keyword is used
            if len(info) == 1 and info[0].lower() == "all":
                l.append([None])
            # else dump each number to the shell
            else:
                l.append([int(s) for s in info])
        # orbital mode
        elif mode.lower() == "o":
            orb.append([int(s) for s in info])
        else:
            raise Exception(f"Unable to decipher tag: {tag}")

    # if something is not used just return None
    if len(l) == 0:
        l = None
    if len(orb) == 0:
        orb = None
    if l is not None and orb is not None:
        raise Exception("Mixed magnetic entity generation is not yet possible!")
    return atom_index, l, orb


def decipher_all_by_pos(
    dh: sisl.physics.Hamiltonian,
    magnetic_entities: list[dict],
    pairs: list[dict],
    atol: float = 1e-4,
    mode="normal",
) -> tuple[list[dict], list[dict]]:
    """This function deciphers the magnetic entities and pairs based on coordinates

    It links the pair information to the magnetic entities based on the
    ordering of the list of magnetic entities and tags. Then it links the
    magnetic entities to the ``sisl`` Hamiltonian indices based on the
    position of atoms.

    Parameters
    ----------
    dh: sisl.physics.Hamiltonian
        The ``sisl`` Hamiltonian to get the positions of atoms
    magnetic_entities: list[dict]
        The list of tags and positions of magnetic entities
    pairs: list[dict]
        The list tags and positions of pairs
    atol: float, optional
        The absolute tolerance between the position from the pair and magnetic entity
        information and the Hamiltonian, by default 1e-4
    mode: {"normal", "full"}, optional
        Whether to return all the information or just the one needed by
        grogupy, by default "normal"

    Returns
    -------
    magnetic_entities: list[dict]
        The 'normalized' magnetic entity information
    pairs: list[dict]
        The 'normalized' pair information
    """

    # iterate over magnetic entities
    for mag_ent in magnetic_entities:
        # get the atom index, by comparing the pair coordinates to the atom
        # coordinates from the sisl Hamiltonian
        atom = np.argwhere(
            np.isclose(mag_ent["xyz"], dh.xyz, atol=atol).sum(axis=1) == 3
        )[0, 0]
        # this must be an integer (really, this is important, because we check the type later)
        mag_ent["atom"] = int(atom)

    # iterate over pairs
    for pair in pairs:
        # get the atom index, by comparing the pair coordinates to the atom
        # coordinates from the sisl Hamiltonian
        # this must be an integer (really, this is important, because we check the type later)
        atom1 = int(
            np.argwhere(np.isclose(pair["xyz1"], dh.xyz, atol=atol).sum(axis=1) == 3)[
                0, 0
            ]
        )
        # this must be an integer (really, this is important, because we check the type later)
        atom2 = int(
            np.argwhere(np.isclose(pair["xyz2"], dh.xyz, atol=atol).sum(axis=1) == 3)[
                0, 0
            ]
        )

        # we have to convert these to indices from the magnetic entity list
        for i, mag_ent in enumerate(magnetic_entities):
            if atom1 == mag_ent["atom"]:
                pair["ai"] = i
            if atom2 == mag_ent["atom"]:
                pair["aj"] = i

    if mode == "normal":
        magnetic_entities = [
            dict(atom=mag_ent["atom"]) for mag_ent in magnetic_entities
        ]
        pairs = [dict(ai=pair["ai"], aj=pair["aj"], Ruc=pair["Ruc"]) for pair in pairs]

        return magnetic_entities, pairs
    elif mode == "full":
        return magnetic_entities, pairs
    else:
        raise Exception("Unknown keyword.")


def decipher_all_by_tag(
    magnetic_entities: list[dict], pairs: list[dict], mode="normal"
) -> tuple[list[dict], list[dict]]:
    """Creates the magnetic entities and pairs from the tag.

    Parameters
    ----------
    magnetic_entities : list[dict]
        List of magnetic entities
    pairs : list[dict]
        List of pairs
    mode : {"normal", "full"}, optional
        Wether to concatenate to the dictionaries or just return the normal input
        for the ``Builder`` class, by default "normal"

    Returns
    -------
    magnetic_entities : list[dict]
        list of magnetic entities in the new format or with the appended information
    pairs : list[dict]
        list of pairs in the new format or with the appended information

    Raises
    ------
    Exception
        Unknown tag
    Exception
        Unknown mode
    """

    # this helper function converts tag to a magnetic entity dictionary

    # iterate over magnetic entities and convert their tags to
    # atom, l and orb
    for mag_ent in magnetic_entities:
        atom, l, orb = decipher(mag_ent["tag"])
        mag_ent["atom"] = atom
        mag_ent["l"] = l
        mag_ent["orb"] = orb

    # iterate over pairs and convert their tags to list indices from the
    # magnetic_entities list
    for pair in pairs:
        tag1 = pair["tag1"]
        tag2 = pair["tag2"]

        for i, mag_ent in enumerate(magnetic_entities):
            if tag1 == mag_ent["tag"]:
                pair["ai"] = i
            if tag2 == mag_ent["tag"]:
                pair["aj"] = i

    if mode == "normal":
        magnetic_entities = [
            dict(atom=mag_ent["atom"], l=mag_ent["l"], orb=mag_ent["orb"])
            for mag_ent in magnetic_entities
        ]
        pairs = [dict(ai=pair["ai"], aj=pair["aj"], Ruc=pair["Ruc"]) for pair in pairs]
        return magnetic_entities, pairs
    elif mode == "full":
        return magnetic_entities, pairs
    else:
        raise Exception("Unknown keyword.")


def strip_dict_structure(
    dictionary: dict,
    pops: list[str] = [
        "_dh",
        "_ds",
        "Gii",
        "Gij",
        "Gji",
        "Vu1",
        "Vu2",
    ],
    setto: Any = [],
) -> dict:
    """Sets the values in the pops keys from the whole dictionary structure to the given value.

    Usually it is used to remove the parts from the magnetic entities and
    the pairs that are taking up a lot of space. See the default keys in
    the pops parameter.

    Parameters
    ----------
    dictionary : dict
        The dictionary structure that we want to strip down
    pops : list[str], optional
        These are the keys that should be set to None in the structure,
        by defualt ["_dh", "_ds", "Gii", "Gij", "Gji", "Vu1", "Vu2"]
    setto : Any, optional
        The value will be set to this, by defualt []

    Returns
    -------
    dict
        The stripped down dictionary
    """
    # create the output dict
    out = dict()
    # iterate over the key value pairs
    for key, value in dictionary.items():
        # if the value at the key is not needed, then set it to None
        if key in pops:
            out_value = setto
        # if the key contains a dictionary go a level deeper and do the same
        elif isinstance(value, dict):
            out_value = strip_dict_structure(value, pops, setto)
        # if the key contains a list, then iterate over it, check if there is any dictionary
        # and if there is, then go a level deeper
        elif isinstance(value, list):
            list_out_val = []
            for val in value:
                if isinstance(val, dict):
                    list_out_val.append(strip_dict_structure(val, pops, setto))
                else:
                    list_out_val.append(val)
            out_value = list_out_val
        # if the key is determined needed then use the key value pair in the out structure
        else:
            out_value = value

        out[key] = out_value
    return out


def standardize_input(input: dict, defaults: dict) -> dict:
    """Standardizes the input from .py and .fdf using the default values


    Parameters
    ----------
    input : dict
        The input dictionary, which may be incomplete
    defaults : dict
        The default input parameters

    Returns
    -------
    dict
        Complete and standardized input dictionary
    """

    for key in input.keys():
        key2 = key.replace("_", "").replace(".", "").lower()
        if key2 in defaults.keys():
            defaults[key2] = input[key]
        else:
            warnings.warn(f"Unrecognized input parameter: {key}")

    if defaults["outfolder"] is None:
        defaults["outfolder"] = defaults["infolder"]
    if defaults["outfile"] is None:
        defaults["outfile"] = (
            f"{defaults['infile'].split('.')[0]}_kset_{'_'.join(map(str, defaults['kset']))}_eset_{defaults['eset']}_{defaults['spinmodel']}"
        )

    return defaults


# default input dictionary
DEFAULT_INPUT = dict(
    infolder="./",
    infile=None,
    kset=None,
    eset=1000,
    esetp=10000,
    emin=None,
    emax=0,
    eminshift=-5,
    emaxshift=0,
    scfxcforientation=[0, 0, 1],
    refxcforientations=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    pairs=None,
    magneticentities=None,
    setupfromrange=None,
    radius=20,
    atomicsubset=None,
    kwargsformagent=dict(l=None),
    maxpairsperloop=1000,
    maxgperloop=1,
    lowmemorymode=False,
    greensfunctionsolver="Parallel",
    applyspinmodel=True,
    spinmodel="generalised-grogu",
    parallelmode=None,
    outmagneticmoment="total",
    savemagnopy=False,
    magnopyprecision=None,
    magnopycomments=True,
    saveuppasd=False,
    uppasdcomments=True,
    savepickle=False,
    picklecompresslevel=3,
    outfolder=None,
    outfile=None,
)
if __name__ == "__main__":
    pass
