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

import numpy as np
import plotly.graph_objects as go
import pytest

import grogupy.viz
from grogupy.physics import Kspace

pytestmark = [pytest.mark.physics]


class TestKspace:
    @pytest.mark.parametrize(
        "kset", [[1, 1, 1], [10, 10, 10], [1, 10, 1], [1, 1, 10], [10, 1, 1]]
    )
    def test_kset_and_NK(self, kset):
        k = Kspace(kset)
        assert k.NK == np.prod(kset)
        assert len(k.kpoints) == np.prod(kset)
        assert len(k.weights) == np.prod(kset)
        k.kset = [100, 100, 100]
        assert k.NK == np.prod([100, 100, 100])
        assert len(k.kpoints) == np.prod([100, 100, 100])
        assert len(k.weights) == np.prod([100, 100, 100])

    @pytest.mark.parametrize(
        "kset", [[1, 1, 1], [10, 10, 10], [1, 10, 1], [1, 1, 10], [10, 1, 1]]
    )
    @pytest.mark.xfail(raises=NotImplementedError)
    def test_kpoints(self, kset):
        k = Kspace(kset)
        raise NotImplementedError

    @pytest.mark.parametrize(
        "kset", [[1, 1, 1], [10, 10, 10], [1, 10, 1], [1, 1, 10], [10, 1, 1]]
    )
    def test_weights(self, kset):
        k = Kspace(kset)
        assert np.allclose(k.weights, 1 / np.prod(kset))
        k.kset = [100, 100, 100]
        assert np.allclose(k.weights, 1 / np.prod([100, 100, 100]))

    def test_equality(self):
        k = Kspace([10, 10, 10])
        k2 = k.copy()
        assert k == k2

        k2.kset = [10, 20, 30]
        assert k != k2
        k2.kset = k.kset
        assert k == k2

    def test_copy(self):
        k = Kspace([10, 10, 10])
        k2 = k.copy()
        assert k == k2
        k2.kset = [1, 1, 1]
        assert k != k2

    def test_plot(self):
        k = Kspace([10, 10, 10])
        assert isinstance(k.plot(), go.Figure)

    def test_getstate_setstate(self):
        k = Kspace([10, 10, 10])
        state = k.__getstate__()
        assert isinstance(state, dict)

        k2 = object.__new__(Kspace)
        k2.__setstate__(state)
        assert k == k2


if __name__ == "__main__":
    pass
