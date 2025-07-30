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
from typing import Union

import numpy as np
from numpy.typing import NDArray

from grogupy._core.utilities import make_kset
from grogupy.batch.timing import DefaultTimer


class Kspace:
    """This class contains and creates the data of the reciprocal space integral.

    Parameters
    ----------
    kset: np.ndarray
        The number of k points in each direction

    Examples
    --------
    Creating a Kspace instance from the minimal amount of information, which
    results in the Gamma point.

    >>> kspace = Kspace()
    >>> kspace.kpoints
    array([[0., 0., 0.]])

    Or create it with some specific data.

    >>> kspace = Kspace(kset=[100,100,1])
    >>> print(kspace)
    <grogupy.Kspace kset=[100 100   1], NK=10000>

    Methods
    -------
    to_dict(all) :
        Returns the instance data as a dictionary.
    copy() :
        Return a copy of this Contour

    Attributes
    ----------
    NK : int, optional
        Total number of kpoints, by default 1
    kset : int, optional
        Number of kpoints in each direction, by default np.array([1,1,1])
    kpoints : NDArray
        The samples in the Brillouin zone
    weights : NDArray
        The weights of the corresponding samples
    times : grogupy.batch.timing.DefaultTimer
        It contains and measures runtime
    """

    def __init__(self, kset: Union[list[int], NDArray] = np.array([1, 1, 1])) -> None:
        """Initialize kspace sampling."""
        self.times: DefaultTimer = DefaultTimer()
        self.__kset: NDArray = np.array(kset, dtype=int)
        self.kpoints: NDArray = make_kset(self.__kset)
        self.weights: NDArray = np.ones(len(self.kpoints)) / len(self.kpoints)
        self.times.measure("setup", restart=True)

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
        if isinstance(value, Kspace):
            if (
                np.allclose(self.__kset, value.__kset)
                and np.allclose(self.kpoints, value.kpoints)
                and np.allclose(self.weights, value.weights)
            ):
                return True
            return False
        return False

    def __repr__(self) -> str:
        """String representation of the instance."""

        out = f"<grogupy.Kspace kset={self.kset}, NK={self.NK}>"

        return out

    @property
    def NK(self):
        """Total number of kpoints."""
        return len(self.kpoints)

    @property
    def kset(self) -> NDArray:
        """Number of kpoints in each direction."""
        return self.__kset

    @kset.setter
    def kset(self, value: Union[list, NDArray]) -> None:
        self.__kset = np.array(value)
        self.kpoints: NDArray = make_kset(self.__kset)
        self.weights: NDArray = np.ones(len(self.kpoints)) / len(self.kpoints)

    def copy(self):
        """Returns the deepcopy of the instance.

        Returns
        -------
        Kspace
            The copied instance.
        """

        return copy.deepcopy(self)


if __name__ == "__main__":
    pass
