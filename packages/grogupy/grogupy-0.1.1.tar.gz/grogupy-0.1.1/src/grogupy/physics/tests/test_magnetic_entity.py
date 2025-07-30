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
import pytest
import sisl

import grogupy
from grogupy._core.utilities import arrays_lists_equal
from grogupy.io.utilities import decipher
from grogupy.physics import MagneticEntity, MagneticEntityList

pytestmark = [pytest.mark.physics, pytest.mark.need_benchmark_data]


class TestMagneticEntity:
    @pytest.mark.parametrize(
        "atom, l, orb, res",
        [
            (None, None, 1, "0Te(o:1)"),
            (None, None, [1], "0Te(o:1)"),
            (None, None, [1, 2], "0Te(o:1-2)"),
            (1, None, None, "1Te(l:All)"),
            (1, None, 1, "1Te(o:1)"),
            (1, None, [1], "1Te(o:1)"),
            (1, None, [1, 2], "1Te(o:1-2)"),
            (1, None, [[1, 2]], "1Te(o:1-2)"),
            (1, 1, None, "1Te(l:1)"),
            (1, [1], None, "1Te(l:1)"),
            (1, [1, 2], None, "1Te(l:1-2)"),
            (1, [[1, 2]], None, "1Te(l:1-2)"),
            ([1], None, None, "1Te(l:All)"),
            ([1], None, 1, "1Te(o:1)"),
            ([1], None, [1], "1Te(o:1)"),
            ([1], None, [1, 2], "1Te(o:1-2)"),
            ([1], None, [[1, 2]], "1Te(o:1-2)"),
            ([1], 1, None, "1Te(l:1)"),
            ([1], [1], None, "1Te(l:1)"),
            ([1], [1, 2], None, "1Te(l:1-2)"),
            ([1], [[1, 2]], None, "1Te(l:1-2)"),
            ([1, 2], None, None, "1Te(l:All)--2Ge(l:All)"),
            ([1, 2], None, 1, "1Te(o:1)--2Ge(o:1)"),
            ([1, 2], None, [1], "1Te(o:1)--2Ge(o:1)"),
            ([1, 2], None, [1, 2], "1Te(o:1-2)--2Ge(o:1-2)"),
            ([1, 2], None, [[1, 2], [1, 2]], "1Te(o:1-2)--2Ge(o:1-2)"),
            ([1, 2], 1, None, "1Te(l:1)--2Ge(l:1)"),
            ([1, 2], [1], None, "1Te(l:1)--2Ge(l:1)"),
            ([1, 2], [1, 2], None, "1Te(l:1-2)--2Ge(l:1-2)"),
            ([1, 2], [[1, 2], [1, 2]], None, "1Te(l:1-2)--2Ge(l:1-2)"),
            # tests from decipher
            ([0], None, [[1]], "0Te(o:1)"),
            ([0], None, [[1, 2]], "0Te(o:1-2)"),
            ([0], [[1]], None, "0Te(l:1)"),
            ([0], [[1, 2]], None, "0Te(l:1-2)"),
            ([0], [[None]], None, "0Te(l:0-1-2-3-4-5-6-7-8-9-10-11-12)"),
            ([1], None, [[1]], "1Te(o:1)"),
            ([1], None, [[1, 2]], "1Te(o:1-2)"),
            ([1], [[1]], None, "1Te(l:1)"),
            ([1], [[1, 2]], None, "1Te(l:1-2)"),
            ([1], [[None]], None, "1Te(l:0-1-2-3-4-5-6-7-8-9-10-11-12)"),
        ],
    )
    def test_generation(self, atom, l, orb, res):
        mag_ent = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom,
            l,
            orb,
        )
        print(mag_ent)
        print(mag_ent._atom, mag_ent._l, mag_ent._spin_box_indices)
        assert mag_ent.tag == res
        print(type(mag_ent._atom), mag_ent._atom)
        assert isinstance(mag_ent._atom, np.ndarray)
        if isinstance(atom, int):
            assert len(mag_ent._atom) == 1
        elif atom is not None:
            assert len(mag_ent._atom) == len(atom)
        assert isinstance(mag_ent._l, list)
        for i in mag_ent._l:
            assert isinstance(i, list)
            for j in i:
                if j is not None:
                    assert isinstance(j, int)
        assert len(mag_ent._spin_box_indices) == mag_ent.SBS
        assert len(mag_ent._tags) == len(mag_ent._atom)
        assert len(mag_ent._xyz) == len(mag_ent._atom)
        assert isinstance(mag_ent._Vu1, list)
        assert isinstance(mag_ent._Vu2, list)
        assert isinstance(mag_ent._Gii, list)
        assert mag_ent.energies is None
        assert mag_ent.K is None
        assert mag_ent.K_consistency is None

    @pytest.mark.parametrize(
        "atom, l, orb",
        [
            (None, None, None),
            (None, None, [[1, 2]]),
            (None, None, [[1, 2], [1, 2]]),
            (None, 1, None),
            (None, 1, 1),
            (None, 1, [1]),
            (None, 1, [1, 2]),
            (None, 1, [[1, 2]]),
            (None, 1, [[1, 2], [1, 2]]),
            (None, [1], None),
            (None, [1], 1),
            (None, [1], [1]),
            (None, [1], [1, 2]),
            (None, [1], [[1, 2]]),
            (None, [1], [[1, 2], [1, 2]]),
            (None, [1, 2], None),
            (None, [1, 2], 1),
            (None, [1, 2], [1]),
            (None, [1, 2], [1, 2]),
            (None, [1, 2], [[1, 2]]),
            (None, [1, 2], [[1, 2], [1, 2]]),
            (None, [[1, 2]], None),
            (None, [[1, 2]], 1),
            (None, [[1, 2]], [1]),
            (None, [[1, 2]], [1, 2]),
            (None, [[1, 2]], [[1, 2]]),
            (None, [[1, 2]], [[1, 2], [1, 2]]),
            (None, [[1, 2], [1, 2]], None),
            (None, [[1, 2], [1, 2]], 1),
            (None, [[1, 2], [1, 2]], [1]),
            (None, [[1, 2], [1, 2]], [1, 2]),
            (None, [[1, 2], [1, 2]], [[1, 2]]),
            (None, [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            (1, 1, 1),
            (1, 1, [1]),
            (1, 1, [1, 2]),
            (1, 1, [[1, 2]]),
            (1, 1, [[1, 2], [1, 2]]),
            (1, [1], 1),
            (1, [1], [1]),
            (1, [1], [1, 2]),
            (1, [1], [[1, 2]]),
            (1, [1], [[1, 2], [1, 2]]),
            (1, [1, 2], 1),
            (1, [1, 2], [1]),
            (1, None, [[1, 2], [1, 2]]),
            (1, [[1, 2], [1, 2]], None),
            (1, [1, 2], [1, 2]),
            (1, [1, 2], [[1, 2]]),
            (1, [1, 2], [[1, 2], [1, 2]]),
            (1, [[1, 2]], 1),
            (1, [[1, 2]], [1]),
            (1, [[1, 2]], [1, 2]),
            (1, [[1, 2]], [[1, 2]]),
            (1, [[1, 2]], [[1, 2], [1, 2]]),
            (1, [[1, 2], [1, 2]], 1),
            (1, [[1, 2], [1, 2]], [1]),
            (1, [[1, 2], [1, 2]], [1, 2]),
            (1, [[1, 2], [1, 2]], [[1, 2]]),
            (1, [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            ([1], None, [[1, 2], [1, 2]]),
            ([1], 1, 1),
            ([1], 1, [1]),
            ([1], 1, [1, 2]),
            ([1], 1, [[1, 2]]),
            ([1], 1, [[1, 2], [1, 2]]),
            ([1], [1], 1),
            ([1], [1], [1]),
            ([1], [1], [1, 2]),
            ([1], [1], [[1, 2]]),
            ([1], [1], [[1, 2], [1, 2]]),
            ([1], [1, 2], 1),
            ([1], [1, 2], [1]),
            ([1], [1, 2], [1, 2]),
            ([1], [1, 2], [[1, 2]]),
            ([1], [1, 2], [[1, 2], [1, 2]]),
            ([1], [[1, 2]], 1),
            ([1], [[1, 2]], [1]),
            ([1], [[1, 2]], [1, 2]),
            ([1], [[1, 2]], [[1, 2]]),
            ([1], [[1, 2]], [[1, 2], [1, 2]]),
            ([1], [[1, 2], [1, 2]], None),
            ([1], [[1, 2], [1, 2]], 1),
            ([1], [[1, 2], [1, 2]], [1]),
            ([1], [[1, 2], [1, 2]], [1, 2]),
            ([1], [[1, 2], [1, 2]], [[1, 2]]),
            ([1], [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            ([1, 2], None, [[1, 2]]),
            ([1, 2], 1, 1),
            ([1, 2], 1, [1]),
            ([1, 2], 1, [1, 2]),
            ([1, 2], 1, [[1, 2]]),
            ([1, 2], 1, [[1, 2], [1, 2]]),
            ([1, 2], [1], 1),
            ([1, 2], [1], [1]),
            ([1, 2], [1], [1, 2]),
            ([1, 2], [1], [[1, 2]]),
            ([1, 2], [1], [[1, 2], [1, 2]]),
            ([1, 2], [1, 2], 1),
            ([1, 2], [1, 2], [1]),
            ([1, 2], [1, 2], [1, 2]),
            ([1, 2], [1, 2], [[1, 2]]),
            ([1, 2], [1, 2], [[1, 2], [1, 2]]),
            ([1, 2], [[1, 2]], None),
            ([1, 2], [[1, 2]], 1),
            ([1, 2], [[1, 2]], [1]),
            ([1, 2], [[1, 2]], [1, 2]),
            ([1, 2], [[1, 2]], [[1, 2]]),
            ([1, 2], [[1, 2]], [[1, 2], [1, 2]]),
            ([1, 2], [[1, 2], [1, 2]], 1),
            ([1, 2], [[1, 2], [1, 2]], [1]),
            ([1, 2], [[1, 2], [1, 2]], [1, 2]),
            ([1, 2], [[1, 2], [1, 2]], [[1, 2]]),
            ([1, 2], [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            ([[1, 2]], None, None),
            ([[1, 2]], None, 1),
            ([[1, 2]], None, [1]),
            ([[1, 2]], None, [1, 2]),
            ([[1, 2]], None, [[1, 2]]),
            ([[1, 2]], None, [[1, 2], [1, 2]]),
            ([[1, 2]], 1, None),
            ([[1, 2]], 1, 1),
            ([[1, 2]], 1, [1]),
            ([[1, 2]], 1, [1, 2]),
            ([[1, 2]], 1, [[1, 2]]),
            ([[1, 2]], 1, [[1, 2], [1, 2]]),
            ([[1, 2]], [1], None),
            ([[1, 2]], [1], 1),
            ([[1, 2]], [1], [1]),
            ([[1, 2]], [1], [1, 2]),
            ([[1, 2]], [1], [[1, 2]]),
            ([[1, 2]], [1], [[1, 2], [1, 2]]),
            ([[1, 2]], [1, 2], None),
            ([[1, 2]], [1, 2], 1),
            ([[1, 2]], [1, 2], [1]),
            ([[1, 2]], [1, 2], [1, 2]),
            ([[1, 2]], [1, 2], [[1, 2]]),
            ([[1, 2]], [1, 2], [[1, 2], [1, 2]]),
            ([[1, 2]], [[1, 2]], None),
            ([[1, 2]], [[1, 2]], 1),
            ([[1, 2]], [[1, 2]], [1]),
            ([[1, 2]], [[1, 2]], [1, 2]),
            ([[1, 2]], [[1, 2]], [[1, 2]]),
            ([[1, 2]], [[1, 2]], [[1, 2], [1, 2]]),
            ([[1, 2]], [[1, 2], [1, 2]], None),
            ([[1, 2]], [[1, 2], [1, 2]], 1),
            ([[1, 2]], [[1, 2], [1, 2]], [1]),
            ([[1, 2]], [[1, 2], [1, 2]], [1, 2]),
            ([[1, 2]], [[1, 2], [1, 2]], [[1, 2]]),
            ([[1, 2]], [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], None, None),
            ([[1, 2], [1, 2]], None, 1),
            ([[1, 2], [1, 2]], None, [1]),
            ([[1, 2], [1, 2]], None, [1, 2]),
            ([[1, 2], [1, 2]], None, [[1, 2]]),
            ([[1, 2], [1, 2]], None, [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], 1, None),
            ([[1, 2], [1, 2]], 1, 1),
            ([[1, 2], [1, 2]], 1, [1]),
            ([[1, 2], [1, 2]], 1, [1, 2]),
            ([[1, 2], [1, 2]], 1, [[1, 2]]),
            ([[1, 2], [1, 2]], 1, [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], [1], None),
            ([[1, 2], [1, 2]], [1], 1),
            ([[1, 2], [1, 2]], [1], [1]),
            ([[1, 2], [1, 2]], [1], [1, 2]),
            ([[1, 2], [1, 2]], [1], [[1, 2]]),
            ([[1, 2], [1, 2]], [1], [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], [1, 2], None),
            ([[1, 2], [1, 2]], [1, 2], 1),
            ([[1, 2], [1, 2]], [1, 2], [1]),
            ([[1, 2], [1, 2]], [1, 2], [1, 2]),
            ([[1, 2], [1, 2]], [1, 2], [[1, 2]]),
            ([[1, 2], [1, 2]], [1, 2], [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], [[1, 2]], None),
            ([[1, 2], [1, 2]], [[1, 2]], 1),
            ([[1, 2], [1, 2]], [[1, 2]], [1]),
            ([[1, 2], [1, 2]], [[1, 2]], [1, 2]),
            ([[1, 2], [1, 2]], [[1, 2]], [[1, 2]]),
            ([[1, 2], [1, 2]], [[1, 2]], [[1, 2], [1, 2]]),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], None),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], 1),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], [1]),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], [1, 2]),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], [[1, 2]]),
            ([[1, 2], [1, 2]], [[1, 2], [1, 2]], [[1, 2], [1, 2]]),
            # tests from decipher
            ([0, 0], [None, None], [[1], [1]]),
            ([0, 0], [None, None], [[1], [1, 2]]),
            ([0, 0], [None, [1]], [[1], None]),
            ([0, 0], [None, [1, 2]], [[1], None]),
            ([0, 0], [None, [None]], [[1], None]),
            ([0, 1], [None, None], [[1], [1]]),
            ([0, 1], [None, None], [[1], [1, 2]]),
            ([0, 1], [None, [1]], [[1], None]),
            ([0, 1], [None, [1, 2]], [[1], None]),
            ([0, 1], [None, [None]], [[1], None]),
        ],
    )
    def test_generation_exception(self, atom, l, orb):
        with pytest.raises(Exception):
            mag_ent = MagneticEntity(
                "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
                atom,
                l,
                orb,
            )
            print(mag_ent)

    @pytest.mark.parametrize(
        "tag1, tag2",
        [
            ("0Te(o:1)", "0Te(o:2)"),
            ("0Te(o:1)", "0Te(l:1)"),
            ("0Te(o:1)", "0Te(l:1-2)"),
            ("0Te(o:1)", "0Te(l:0-1-2-3-4-5-6-7-8-9-10-11-12)"),
            ("0Te(o:1)", "1Te(l:1)"),
            ("0Te(o:1)", "1Te(l:1-2)"),
            ("0Te(o:1)", "1Te(l:0-1-2-3-4-5-6-7-8-9-10-11-12)"),
        ],
    )
    def test_addition(self, tag1, tag2):
        atom1, l1, orb1 = decipher(tag1)
        atom2, l2, orb2 = decipher(tag2)
        mag_ent1 = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom1,
            l1,
            orb1,
        )
        mag_ent2 = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom2,
            l2,
            orb2,
        )

        new = mag_ent1 + mag_ent2
        assert new.tag == tag1 + "--" + tag2
        assert arrays_lists_equal(
            new._atom, np.hstack((mag_ent1._atom, mag_ent2._atom))
        )
        assert new._l == mag_ent1._l + mag_ent2._l
        assert arrays_lists_equal(
            new._orbital_box_indices,
            np.hstack((mag_ent1._orbital_box_indices, mag_ent2._orbital_box_indices)),
        )
        assert arrays_lists_equal(
            new._spin_box_indices,
            np.hstack((mag_ent1._spin_box_indices, mag_ent2._spin_box_indices)),
        )
        assert arrays_lists_equal(new._xyz, np.vstack((mag_ent1._xyz, mag_ent2._xyz)))

    def test_reset(self):
        mag_ent = grogupy.load("./benchmarks/test_magnetic_entity.pkl")

        mag_ent._Vu1 = 1
        mag_ent._Vu2 = None
        mag_ent._Gii = np.array([10])
        mag_ent.energies = 3.14
        mag_ent.K = (10, 20, 30)
        mag_ent.K_consistency = 2

        mag_ent.reset()
        assert mag_ent._Vu1 == []
        assert mag_ent._Vu2 == []
        assert mag_ent._Gii == []
        assert mag_ent.energies is None
        assert mag_ent.K is None
        assert mag_ent.K_consistency is None

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_add_G_tmp(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_energies(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_anisotropy(self):
        raise NotImplementedError

    @pytest.mark.parametrize(
        "atom, l, orb",
        [
            (None, None, 1),
            (None, None, [1]),
            (None, None, [1, 2]),
            (1, None, None),
            (1, None, 1),
            (1, None, [1]),
            (1, None, [1, 2]),
            (1, None, [[1, 2]]),
            (1, 1, None),
            (1, [1], None),
            (1, [1, 2], None),
            (1, [[1, 2]], None),
            ([1], None, None),
            ([1], None, 1),
            ([1], None, [1]),
            ([1], None, [1, 2]),
            ([1], None, [[1, 2]]),
            ([1], 1, None),
            ([1], [1], None),
            ([1], [1, 2], None),
            ([1], [[1, 2]], None),
            ([1, 2], None, None),
            ([1, 2], None, 1),
            ([1, 2], None, [1]),
            ([1, 2], None, [1, 2]),
            ([1, 2], None, [[1, 2], [1, 2]]),
            ([1, 2], 1, None),
            ([1, 2], [1], None),
            ([1, 2], [1, 2], None),
            ([1, 2], [[1, 2], [1, 2]], None),
            # tests from decipher
            ([0], None, [[1]]),
            ([0], None, [[1, 2]]),
            ([0], [[1]], None),
            ([0], [[1, 2]], None),
            ([0], [[None]], None),
            ([1], None, [[1]]),
            ([1], None, [[1, 2]]),
            ([1], [[1]], None),
            ([1], [[1, 2]], None),
            ([1], [[None]], None),
        ],
    )
    def test_equality(self, atom, l, orb):
        m = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom,
            l,
            orb,
        )

        m2 = m.copy()
        assert m == m2

        m2._dh = sisl.get_sile("./benchmarks/CrI3/CrI3.fdf").read_hamiltonian()
        assert m != m2
        m2._dh = m._dh
        assert m == m2

        m2._ds = sisl.get_sile("./benchmarks/CrI3/CrI3.fdf").read_density_matrix()
        assert m != m2
        m2._ds = m._ds
        assert m == m2

        m2.infile = "unknown!"  # lowercase
        assert m != m2
        m2.infile = m.infile
        assert m == m2

        m2._atom = np.array([1000])
        assert m != m2
        m2._atom = m._atom
        assert m == m2

        m2._l = [None, [None, 10]]
        assert m != m2
        m2._l = m._l
        assert m == m2

        m2._orbital_box_indices = [0]
        assert m != m2
        m2._orbital_box_indices = m._orbital_box_indices
        assert m == m2

        m2._tags = "asd"
        assert m != m2
        m2._tags = m._tags
        assert m == m2

        m2._local_mulliken = np.zeros_like(m._local_mulliken)
        assert m != m2
        m2._local_mulliken = m._local_mulliken
        assert m == m2

        m2._total_mulliken = np.zeros_like(m._total_mulliken)
        assert m != m2
        m2._total_mulliken = m._total_mulliken
        assert m == m2

        m2._spin_box_indices = np.ones_like(m._spin_box_indices)
        assert m != m2
        m2._spin_box_indices = m._spin_box_indices
        assert m == m2

        m2._xyz[-1] = np.zeros(3)
        assert m != m2
        m2._xyz = m._xyz
        assert m == m2

        m2._Vu1 = np.zeros(3)
        assert m != m2
        m2._Vu1 = m._Vu1
        assert m == m2

        m2._Vu2 = np.zeros(3)
        assert m != m2
        m2._Vu2 = m._Vu2
        assert m == m2

        m2._Gii = [np.zeros(3)]
        assert m != m2
        m2._Gii = m._Gii
        assert m == m2

        m2.energies = np.zeros(3)
        assert m != m2
        m2.energies = m.energies
        assert m == m2

        m2.K = []
        assert m != m2
        m2.K = m.K
        assert m == m2

        m2.K_consistency = 1000
        assert m != m2
        m2.K_consistency = m.K_consistency
        assert m == m2

    @pytest.mark.parametrize(
        "atom, l, orb",
        [
            (None, None, 1),
            (None, None, [1]),
            (None, None, [1, 2]),
            (1, None, None),
            (1, None, 1),
            (1, None, [1]),
            (1, None, [1, 2]),
            (1, None, [[1, 2]]),
            (1, 1, None),
            (1, [1], None),
            (1, [1, 2], None),
            (1, [[1, 2]], None),
            ([1], None, None),
            ([1], None, 1),
            ([1], None, [1]),
            ([1], None, [1, 2]),
            ([1], None, [[1, 2]]),
            ([1], 1, None),
            ([1], [1], None),
            ([1], [1, 2], None),
            ([1], [[1, 2]], None),
            ([1, 2], None, None),
            ([1, 2], None, 1),
            ([1, 2], None, [1]),
            ([1, 2], None, [1, 2]),
            ([1, 2], None, [[1, 2], [1, 2]]),
            ([1, 2], 1, None),
            ([1, 2], [1], None),
            ([1, 2], [1, 2], None),
            ([1, 2], [[1, 2], [1, 2]], None),
            # tests from decipher
            ([0], None, [[1]]),
            ([0], None, [[1, 2]]),
            ([0], [[1]], None),
            ([0], [[1, 2]], None),
            ([0], [[None]], None),
            ([1], None, [[1]]),
            ([1], None, [[1, 2]]),
            ([1], [[1]], None),
            ([1], [[1, 2]], None),
            ([1], [[None]], None),
        ],
    )
    def test_copy(self, atom, l, orb):
        m = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom,
            l,
            orb,
        )
        m2 = m.copy()
        assert m == m2
        m2._tags = 1
        assert m != m2

    @pytest.mark.parametrize(
        "atom, l, orb",
        [
            (None, None, 1),
            (None, None, [1]),
            (None, None, [1, 2]),
            (1, None, None),
            (1, None, 1),
            (1, None, [1]),
            (1, None, [1, 2]),
            (1, None, [[1, 2]]),
            (1, 1, None),
            (1, [1], None),
            (1, [1, 2], None),
            (1, [[1, 2]], None),
            ([1], None, None),
            ([1], None, 1),
            ([1], None, [1]),
            ([1], None, [1, 2]),
            ([1], None, [[1, 2]]),
            ([1], 1, None),
            ([1], [1], None),
            ([1], [1, 2], None),
            ([1], [[1, 2]], None),
            ([1, 2], None, None),
            ([1, 2], None, 1),
            ([1, 2], None, [1]),
            ([1, 2], None, [1, 2]),
            ([1, 2], None, [[1, 2], [1, 2]]),
            ([1, 2], 1, None),
            ([1, 2], [1], None),
            ([1, 2], [1, 2], None),
            ([1, 2], [[1, 2], [1, 2]], None),
            # tests from decipher
            ([0], None, [[1]]),
            ([0], None, [[1, 2]]),
            ([0], [[1]], None),
            ([0], [[1, 2]], None),
            ([0], [[None]], None),
            ([1], None, [[1]]),
            ([1], None, [[1, 2]]),
            ([1], [[1]], None),
            ([1], [[1, 2]], None),
            ([1], [[None]], None),
        ],
    )
    def test_getstate_setstate(self, atom, l, orb):
        m = MagneticEntity(
            "./benchmarks/Fe3GeTe2/Fe3GeTe2.fdf",
            atom,
            l,
            orb,
        )
        state = m.__getstate__()
        assert isinstance(state, dict)

        m2 = object.__new__(MagneticEntity)
        m2.__setstate__(state)
        assert m == m2


class TestMagneticEntityList:
    def test_properties(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList(system.magnetic_entities)

        assert len(system.magnetic_entities) == len(mlist)
        for m1, m2 in zip(system.magnetic_entities, mlist):
            assert m1 == m2

    def test_getitem(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList(system.magnetic_entities)

        assert system.magnetic_entities[0] == mlist[0]
        assert system.magnetic_entities[1] == mlist[1]

    def test_getattr(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList(system.magnetic_entities)

        ani = []
        for m in system.magnetic_entities:
            ani.append(m.K)

        assert (mlist.K == np.array(ani)).all()

    def test_append(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList()

        for m in system.magnetic_entities:
            mlist.append(m)
        assert len(mlist) == len(system.magnetic_entities)

    def test_tolist(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList(system.magnetic_entities)

        assert isinstance(mlist, MagneticEntityList)
        assert isinstance(mlist.tolist(), list)

    def test_toarray(self):
        system = grogupy.load("./benchmarks/test_builder.pkl")
        system.magnetic_entities = system.magnetic_entities.tolist()
        mlist = MagneticEntityList(system.magnetic_entities)

        assert isinstance(mlist, MagneticEntityList)
        assert isinstance(mlist.toarray(), np.ndarray)


if __name__ == "__main__":
    pass
