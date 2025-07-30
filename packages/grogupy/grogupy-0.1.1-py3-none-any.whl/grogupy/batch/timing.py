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

from time import time


class DefaultTimer:
    """This class measures and stores the runtime of each object.

    Upon initialization the clock is started.

    Methods
    -------
    restart() :
        It restarts the timer
    measure(function) :
        It measures the runtime and writes to times[function]

    Attributes
    ----------
    times: dict
        It contains the runtimes
    """

    def __init__(self):
        """Initialize timer."""
        self.__start_measure: float = time()
        self._times: dict = dict()

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__start_measure = state["_DefaultTimer__start_measure"]
        self._times = state["_times"]

    def __eq__(self, value):
        if isinstance(value, DefaultTimer):
            if (
                self.__start_measure == value.__start_measure
                and self.times == value.times
            ):
                return True
            return False
        return False

    @property
    def times(self) -> dict:
        return self._times

    def restart(self) -> None:
        """Resets the measurement time."""

        self.__start_measure = time()

    def measure(self, key: str, restart: bool = False) -> None:
        """Saves the measurement time.

        It dumps the difference between the current time and the time
        the measurement is started or reset in the instance variable
        `times` with the key `key`. If `restart` is true, then it
        resets the timer.

        Parameters
        ----------
        key: str
            Key to the instance dictionary
        restart: bool, optional
            If it is true, the timer is reset, by default False
        """

        current = time()
        self._times[key] = current - self.__start_measure
        if restart:
            self.__start_measure = time()


if __name__ == "__main__":
    pass
