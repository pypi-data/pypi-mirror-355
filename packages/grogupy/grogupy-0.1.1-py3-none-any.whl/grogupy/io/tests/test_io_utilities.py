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

from grogupy.io.utilities import *

pytestmark = [pytest.mark.io]


class TestUtilities:
    @pytest.mark.parametrize(
        "tag, atom, l, orb",
        [
            ("0Te(o:1)", [0], None, [[1]]),
            ("0Te(o:1-2)", [0], None, [[1, 2]]),
            ("0Te(l:1)", [0], [[1]], None),
            ("0Te(l:1-2)", [0], [[1, 2]], None),
            ("0Te(l:All)", [0], [[None]], None),
            ("1Te(o:1)", [1], None, [[1]]),
            ("1Te(o:1-2)", [1], None, [[1, 2]]),
            ("1Te(l:1)", [1], [[1]], None),
            ("1Te(l:1-2)", [1], [[1, 2]], None),
            ("1Te(l:All)", [1], [[None]], None),
            ("0Te(o:1)--0Te(o:1)", [0, 0], None, [[1], [1]]),
            ("0Te(o:1)--0Te(o:1-2)", [0, 0], None, [[1], [1, 2]]),
            ("0Te(o:1)--1Te(o:1)", [0, 1], None, [[1], [1]]),
            ("0Te(o:1)--1Te(o:1-2)", [0, 1], None, [[1], [1, 2]]),
        ],
    )
    def test_decipher(self, tag, atom, l, orb):
        catom, cl, corb = decipher(tag)

        print(catom, atom)
        print(cl, l)
        print(corb, orb)

        assert catom == atom
        assert cl == l
        assert corb == orb

    @pytest.mark.parametrize(
        "tag",
        [
            ("0Te(a:1)"),
            ("Te(o:1)"),
            ("0Te(o:all)"),
            ("0Te(l:allee)"),
            ("0Te(l:allee-allee)"),
            ("0Te(l:allee--allee)"),
            ("0Te(o:1)--0Te(l:1)"),
            ("0Te(o:1)--0Te(l:1-2)"),
            ("0Te(o:1)--0Te(l:All)"),
            ("0Te(o:1)--1Te(l:1)"),
            ("0Te(o:1)--1Te(l:1-2)"),
            ("0Te(o:1)--1Te(l:All)"),
        ],
    )
    def test_raise_decipher(self, tag):
        with pytest.raises(Exception):
            atom, l, orb = decipher(tag)
            print(atom, l, orb)

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_decipher_all_by_pos(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_decipher_all_by_tag(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_strip_dict_structure(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_standardize_input(self):
        raise NotImplementedError


if __name__ == "__main__":
    pass
