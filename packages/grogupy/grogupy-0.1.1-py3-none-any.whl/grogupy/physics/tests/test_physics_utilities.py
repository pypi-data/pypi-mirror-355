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

import pytest

from grogupy.physics.utilities import *

pytestmark = [pytest.mark.physics]


class TestUtilities:
    @pytest.mark.xfail(raises=NotImplementedError)
    def test_get_number_of_electrons(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_automatic_emin(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_blow_up_orbindx(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_spin_tracer(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_parse_magnetic_entity(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_interaction_energy(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_second_order_energy(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_calculate_anisotropy_tensor(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_fit_anisotropy_tensor(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_calculate_exchange_tensor(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_fit_exchange_tensor(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_calculate_isotropic_only(self):
        raise NotImplementedError


if __name__ == "__main__":
    pass
