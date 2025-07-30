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

from grogupy._core.utilities import make_contour
from grogupy.batch.timing import DefaultTimer

from .utilities import automatic_emin


class Contour:
    """This class contains and creates the data of the energy contour for the integration.

    If the ``emin`` argument is not given the ``eigfile`` argument
    must be given to automatically set the energy minimum of the system.

    Parameters
    ----------
    eset : int
        Number of energy samples on the contour
    esetp : float
        A parameters that changes the shape of the sampling
    emin : Union[float, None]
        The lower bound of the integral. When it is `None` it is automatically set
    emax : Union[float, None], optional
        The upper bound of the integral, by default 0
    emin_shift : float
        It is added to the emin value, by default -5
    emax_shift : float
        It is added to the emax value, by default 0
    eigfile : Union[str, None]
        Either the path to the siesta .EIG or the .fdf file

    Examples
    --------
    Creating a Contour instance from the minimal amount of information.

    >>> contour = Contour(eset=600, esetp=1000, emin=-20)
    >>> print(contour)
    <grogupy.Contour emin=-25, emax=0, eset=600, esetp=1000>

    Or create it with the automatic emin finder.

    >>> contour = Contour(eset=600, esetp=1000, emin=None, eigfile="/Users/danielpozsar/Downloads/Fe3GeTe2/Fe3GeTe2.fdf")
    >>> print(contour)
    <grogupy.Contour emin=-17.80687896, emax=0, eset=600, esetp=1000>

    Methods
    -------
    to_dict() :
        Returns the instance data as a dictionary.
    copy() :
        Return a copy of this Contour

    Attributes
    ----------
    samples: NDArray
        The samples along the contour
    weights: NDArray
        The weights of the corresponding samples
    times: grogupy.batch.timing.DefaultTimer
        It contains and measures runtime
    """

    def __init__(
        self,
        eset: int,
        esetp: float,
        emin: Union[float, None] = None,
        emax: float = 0,
        emin_shift: float = -5,
        emax_shift: float = 0,
        eigfile: Union[str, None] = None,
    ) -> None:
        """This functions sets up the energy integral.

        If the ``emin`` argument is not given the ``eigfile`` argument
        must be given to automatically set the energy minimum of the system.

        Parameters
        ----------
        eset : int
            Number of energy samples on the contour
        esetp : float
            A parameters that changes the shape of the sampling
        emin : Union[float, None]
            The lower bound of the integral. When it is `None` it is automatically set
        emax : Union[float, None], optional
            The upper bound of the integral, by default 0
        emin_shift : float
            It is added to the emin value, by default -5
        emax_shift : float
            It is added to the emax value, by default 0
        eigfile : Union[str, None]
            Either the path to the siesta .EIG or the .fdf file
        """

        self.times: DefaultTimer = DefaultTimer()
        self.__automatic_emin: bool = False
        self._eigfile: Union[str, None] = eigfile

        if emin is None:
            if self._eigfile is None:
                raise Exception("Eigfile is needed for automatic emin!")
            else:
                self._emin: float = automatic_emin(self._eigfile)
                self.__automatic_emin = True
        else:
            self._emin: float = emin
        self._emax: float = emax

        self._emin += emin_shift
        self._emax += emax_shift

        self._eset: int = eset
        self._esetp: float = esetp
        self.samples: NDArray = np.empty(1)
        self.weights: NDArray = np.empty(1)
        self.__make_contour()
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

    def __repr__(self) -> str:
        """String representation of the instance."""

        out = f"<grogupy.Contour emin={self.emin}, emax={self.emax}, eset={self.eset}, esetp={self.esetp}>"

        return out

    def __eq__(self, value):
        if isinstance(value, Contour):
            if (
                self.__automatic_emin == value.__automatic_emin
                and self._eigfile == value._eigfile
                and self._emin == value._emin
                and self._emax == value._emax
                and self._eset == value._eset
                and self._esetp == value._esetp
                and np.allclose(self.samples, value.samples)
                and np.allclose(self.weights, value.weights)
            ):
                return True
            else:
                return False
        else:
            return False

    @property
    def automatic_emin(self) -> bool:
        return self.__automatic_emin

    @property
    def emin(self) -> float:
        """Bottom of the contour integral."""
        return self._emin

    @property
    def emax(self) -> float:
        """Top of the contour integral."""
        return self._emax

    @property
    def eset(self) -> int:
        """Number of samples along the contour."""
        return self._eset

    @property
    def esetp(self) -> float:
        """Assymmetry parameter of the contour generation."""
        return self._esetp

    @emin.setter
    def emin(self, value: float) -> None:
        self._emin = value
        self.__make_contour()

    @emax.setter
    def emax(self, value: float) -> None:
        self._emax = value
        self.__make_contour()

    @eset.setter
    def eset(self, value: int) -> None:
        self._eset = value
        self.__make_contour()

    @esetp.setter
    def esetp(self, value: float) -> None:
        self._esetp = value
        self.__make_contour()

    def __make_contour(self) -> None:
        """It calculates the samples and weights.

        It calculates the samples and weights based on the instance attributes
        and dumps them to the instance attributes `samples` and `weights`.
        """

        ze, we = make_contour(self.emin, self.emax, self.eset, self.esetp)
        self.samples: NDArray = ze
        self.weights: NDArray = we

    def copy(self):
        """Returns the deepcopy of the instance.

        Returns
        -------
        Contour
            The copied instance.
        """

        return copy.deepcopy(self)


if __name__ == "__main__":
    pass
