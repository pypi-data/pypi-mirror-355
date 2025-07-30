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

import plotly.graph_objects as go
import pytest

import grogupy.viz
from grogupy.physics import Contour

pytestmark = [pytest.mark.physics]


class TestContour:
    @pytest.mark.parametrize("eset", [1, 10, 100])
    def test_eset(self, eset):
        c = Contour(eset, 1000, emin=0)
        assert len(c.samples) == eset
        assert len(c.weights) == eset
        c.eset = 10
        assert len(c.samples) == 10
        assert len(c.weights) == 10

    @pytest.mark.parametrize("emin", [-10, -0.1, 0, 1, 1.2])
    @pytest.mark.parametrize("eset", [1, 10, 100, 500, 1000])
    def test_emin(self, emin, eset):
        c = Contour(eset, 10000, emin)
        assert (emin - 5) <= c.samples.real.min()
        c.emin = -100
        assert -100 <= c.samples.real.min()

    @pytest.mark.parametrize("emax", [-10, -0.1, 0, 1, 1.2])
    @pytest.mark.parametrize("eset", [1, 10, 100, 500, 1000])
    def test_emax(self, emax, eset):
        c = Contour(eset, 10000, emin=-100, emax=emax)
        assert c.samples.real.max() <= emax or (c.samples.real.max() - emax) < 1e-14
        c.emax = 100
        assert c.samples.real.max() <= 100 or (c.samples.real.max() - 100) < 1e-14

    def test_equality(self):
        c = Contour(100, 1000, emin=-10)
        c2 = c.copy()
        assert c == c2

        c2._eigfile = "None"
        assert c != c2
        c2._eigfile = c._eigfile
        assert c == c2

        c2.emin = -100
        assert c != c2
        c2.emin = c.emin
        assert c == c2

        c2.emax = 0.0000000001
        assert c != c2
        c2.emax = c.emax
        assert c == c2

        c2._Contour__automatic_emin = True
        assert c != c2
        c2._Contour__automatic_emin = c._Contour__automatic_emin
        assert c == c2

        c2.eset = 10
        assert c != c2
        c2.eset = c.eset
        assert c == c2

        c2.esetp = 100000000
        assert c != c2
        c2.esetp = c.esetp
        assert c == c2

        c2.samples = c.samples - 0.001
        assert c != c2
        c2.samples = c.samples
        assert c == c2

        c2.weights = c.weights - 0.001
        assert c != c2
        c2.weights = c.weights
        assert c == c2

    def test_copy(self):
        c = Contour(100, 1000, emin=-10)
        c2 = c.copy()
        assert c == c2
        c2.emax = 1
        assert c != c2

    def test_plot(self):
        c = Contour(100, 1000, emin=-10)
        assert isinstance(c.plot(), go.Figure)

    def test_getstate_setstate(self):
        c = Contour(100, 1000, emin=-10)
        state = c.__getstate__()
        assert isinstance(state, dict)

        c2 = object.__new__(Contour)
        c2.__setstate__(state)
        assert c == c2


if __name__ == "__main__":
    pass
