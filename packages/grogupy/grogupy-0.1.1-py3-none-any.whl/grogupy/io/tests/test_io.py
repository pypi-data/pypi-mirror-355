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

import os
import pickle

import pytest

import grogupy
import grogupy.batch
from grogupy.io.io import *

pytestmark = [pytest.mark.io, pytest.mark.need_benchmark_data]


# cleaning up possible temorary output files
@pytest.fixture(autouse=True)
def clean():
    yield
    if os.path.isfile("./benchmarks/test_magnopy.magnopy.txt"):
        os.remove("./benchmarks/test_magnopy.magnopy.txt")
    if os.path.isfile("./benchmarks/test_pair_temp.pkl"):
        os.remove("./benchmarks/test_pair_temp.pkl")
    if os.path.isfile("./benchmarks/test_magnetic_entity_temp.pkl"):
        os.remove("./benchmarks/test_magnetic_entity_temp.pkl")
    if os.path.isfile("./benchmarks/test_default_timer_temp.pkl"):
        os.remove("./benchmarks/test_default_timer_temp.pkl")
    if os.path.isfile("./benchmarks/test_kspace_temp.pkl"):
        os.remove("./benchmarks/test_kspace_temp.pkl")
    if os.path.isfile("./benchmarks/test_contour_temp.pkl"):
        os.remove("./benchmarks/test_contour_temp.pkl")
    if os.path.isfile("./benchmarks/test_hamiltonian_temp.pkl"):
        os.remove("./benchmarks/test_hamiltonian_temp.pkl")
    if os.path.isfile("./benchmarks/test_builder_temp.pkl"):
        os.remove("./benchmarks/test_builder_temp.pkl")
    if os.path.isfile("./benchmarks/test_builder_temp2.pkl"):
        os.remove("./benchmarks/test_builder_temp2.pkl")


class TestIO:
    def test_load_save(self):
        builder = grogupy.load("./benchmarks/test_builder.pkl")
        assert isinstance(builder, grogupy.Builder)
        grogupy.save(builder, "./benchmarks/test_builder_temp.pkl", compress=0)
        builder2 = grogupy.load("./benchmarks/test_builder_temp.pkl")
        assert isinstance(builder2, grogupy.Builder)
        assert builder == builder2

        hamiltonian = grogupy.load("./benchmarks/test_hamiltonian.pkl")
        assert isinstance(hamiltonian, grogupy.Hamiltonian)
        grogupy.save(hamiltonian, "./benchmarks/test_hamiltonian_temp.pkl", compress=0)
        hamiltonian2 = grogupy.load("./benchmarks/test_hamiltonian_temp.pkl")
        assert isinstance(hamiltonian2, grogupy.Hamiltonian)
        assert hamiltonian == hamiltonian2

        contour = grogupy.load("./benchmarks/test_contour.pkl")
        assert isinstance(contour, grogupy.Contour)
        grogupy.save(contour, "./benchmarks/test_contour_temp.pkl", compress=0)
        contour2 = grogupy.load("./benchmarks/test_contour_temp.pkl")
        assert isinstance(contour2, grogupy.Contour)
        assert contour == contour2

        kspace = grogupy.load("./benchmarks/test_kspace.pkl")
        assert isinstance(kspace, grogupy.Kspace)
        grogupy.save(kspace, "./benchmarks/test_kspace_temp.pkl", compress=0)
        kspace2 = grogupy.load("./benchmarks/test_kspace_temp.pkl")
        assert isinstance(kspace2, grogupy.Kspace)
        assert kspace == kspace2

        default_timer = grogupy.load("./benchmarks/test_default_timer.pkl")
        assert isinstance(default_timer, grogupy.batch.DefaultTimer)
        grogupy.save(
            default_timer, "./benchmarks/test_default_timer_temp.pkl", compress=0
        )
        default_timer2 = grogupy.load("./benchmarks/test_default_timer_temp.pkl")
        assert isinstance(default_timer2, grogupy.batch.DefaultTimer)
        assert default_timer == default_timer2

        mag_ent = grogupy.load("./benchmarks/test_magnetic_entity.pkl")
        assert isinstance(mag_ent, grogupy.MagneticEntity)
        grogupy.save(mag_ent, "./benchmarks/test_magnetic_entity_temp.pkl", compress=0)
        mag_ent2 = grogupy.load("./benchmarks/test_magnetic_entity_temp.pkl")
        assert isinstance(mag_ent2, grogupy.MagneticEntity)
        assert mag_ent == mag_ent2

        pair = grogupy.load("./benchmarks/test_pair.pkl")
        assert isinstance(pair, grogupy.Pair)
        grogupy.save(pair, "./benchmarks/test_pair_temp.pkl", compress=0)
        pair2 = grogupy.load("./benchmarks/test_pair_temp.pkl")
        assert isinstance(pair2, grogupy.Pair)
        assert pair == pair2

    def test_load_save_Builder(self):
        builder = load_Builder("./benchmarks/test_builder.pkl")
        assert isinstance(builder, grogupy.Builder)
        grogupy.save(builder, "./benchmarks/test_builder_temp.pkl", compress=0)
        builder2 = grogupy.load("./benchmarks/test_builder_temp.pkl")
        assert isinstance(builder2, grogupy.Builder)
        assert builder == builder2

    def test_load_save_Hamiltonian(self):
        hamiltonian = load_Hamiltonian("./benchmarks/test_hamiltonian.pkl")
        assert isinstance(hamiltonian, grogupy.Hamiltonian)
        grogupy.save(hamiltonian, "./benchmarks/test_hamiltonian_temp.pkl", compress=0)
        hamiltonian2 = grogupy.load("./benchmarks/test_hamiltonian_temp.pkl")
        assert isinstance(hamiltonian2, grogupy.Hamiltonian)
        assert hamiltonian == hamiltonian2

    def test_load_save_Contour(self):
        contour = load_Contour("./benchmarks/test_contour.pkl")
        assert isinstance(contour, grogupy.Contour)
        grogupy.save(contour, "./benchmarks/test_contour_temp.pkl", compress=0)
        contour2 = grogupy.load("./benchmarks/test_contour_temp.pkl")
        print(type(contour2))
        assert isinstance(contour2, grogupy.Contour)
        assert contour == contour2

    def test_load_save_Kspace(self):
        kspace = load_Kspace("./benchmarks/test_kspace.pkl")
        assert isinstance(kspace, grogupy.Kspace)
        grogupy.save(kspace, "./benchmarks/test_kspace_temp.pkl", compress=0)
        kspace2 = grogupy.load("./benchmarks/test_kspace_temp.pkl")
        assert isinstance(kspace2, grogupy.Kspace)
        assert kspace == kspace2

    def test_load_save_DefaultTimer(self):
        default_timer = load_DefaultTimer("./benchmarks/test_default_timer.pkl")
        assert isinstance(default_timer, grogupy.batch.DefaultTimer)
        grogupy.save(
            default_timer, "./benchmarks/test_default_timer_temp.pkl", compress=0
        )
        default_timer2 = grogupy.load("./benchmarks/test_default_timer_temp.pkl")
        assert isinstance(default_timer2, grogupy.batch.DefaultTimer)
        assert default_timer == default_timer2

    def test_load_save_MagneticEntity(self):
        magnetic_entity = load_MagneticEntity("./benchmarks/test_magnetic_entity.pkl")
        assert isinstance(magnetic_entity, grogupy.MagneticEntity)
        grogupy.save(
            magnetic_entity, "./benchmarks/test_magnetic_entity_temp.pkl", compress=0
        )
        magnetic_entity2 = grogupy.load("./benchmarks/test_magnetic_entity_temp.pkl")
        assert isinstance(magnetic_entity2, grogupy.MagneticEntity)
        assert magnetic_entity == magnetic_entity2

    def test_load_save_Pair(self):
        pair = load_Pair("./benchmarks/test_pair.pkl")
        assert isinstance(pair, grogupy.Pair)
        grogupy.save(pair, "./benchmarks/test_pair_temp.pkl", compress=0)
        pair2 = grogupy.load("./benchmarks/test_pair_temp.pkl")
        assert isinstance(pair2, grogupy.Pair)
        assert pair == pair2

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_load_save_magnopy(self):
        builder = load_Builder("./benchmarks/test_builder.pkl")
        save_magnopy(builder, "./benchmarks/test_magnopy")
        data = read_magnopy("./benchmarks/test_magnopy.magnopy.txt")
        print(data)
        raise NotImplementedError

    def test_save_UppASD(self):
        builder = load_Builder("./benchmarks/test_builder.pkl")
        os.mkdir("./src/grogupy/io/tests/test_UppASD")
        save_UppASD(builder, "./src/grogupy/io/tests/test_UppASD")
        assert os.path.isdir("./src/grogupy/io/tests/test_UppASD")
        assert os.path.isfile("./src/grogupy/io/tests/test_UppASD/jfile")
        assert os.path.isfile("./src/grogupy/io/tests/test_UppASD/momfile")
        assert os.path.isfile("./src/grogupy/io/tests/test_UppASD/posfile")
        assert os.path.isfile("./src/grogupy/io/tests/test_UppASD/cell.tmp.txt")
        os.remove("./src/grogupy/io/tests/test_UppASD/jfile")
        os.remove("./src/grogupy/io/tests/test_UppASD/momfile")
        os.remove("./src/grogupy/io/tests/test_UppASD/posfile")
        os.remove("./src/grogupy/io/tests/test_UppASD/cell.tmp.txt")
        os.rmdir("./src/grogupy/io/tests/test_UppASD")

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_read_fdf(self):
        raise NotImplementedError

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_py(self):
        raise NotImplementedError

    def test_save_compression(self):
        def parse(dictionary, key):
            out = []
            if isinstance(dictionary, dict):
                for k, v in dictionary.items():
                    if k == key:
                        out.append(v)
                    elif isinstance(v, dict) or isinstance(v, list):
                        small_out = parse(v, key)
                        for d in small_out:
                            out.append(d)
            elif isinstance(dictionary, list):
                for v in dictionary:
                    if isinstance(v, dict) or isinstance(v, list):
                        small_out = parse(v, key)
                        for d in small_out:
                            out.append(d)
            return out

        builder = grogupy.load("./benchmarks/test_builder.pkl")
        assert isinstance(builder, grogupy.Builder)

        grogupy.save(builder, "./benchmarks/test_builder_temp2.pkl", compress=0)
        with open("./benchmarks/test_builder_temp2.pkl", "rb") as f:
            dictionary = pickle.load(f)
        import sys

        assert sys.getsizeof(dictionary) == sys.getsizeof(builder.__dict__)

        grogupy.save(builder, "./benchmarks/test_builder_temp2.pkl", compress=1)
        with open("./benchmarks/test_builder_temp2.pkl", "rb") as f:
            dictionary = pickle.load(f)
        dat = []
        temp = parse(dictionary, "_dh")
        for t in temp:
            dat.append(t)
        temp = parse(dictionary, "_ds")
        for t in temp:
            dat.append(t)
        for d in dat:
            assert d is None

        grogupy.save(builder, "./benchmarks/test_builder_temp2.pkl", compress=2)
        with open("./benchmarks/test_builder_temp2.pkl", "rb") as f:
            dictionary = pickle.load(f)
        dat = []
        temp = parse(dictionary, "_dh")
        for t in temp:
            dat.append(t)
        temp = parse(dictionary, "_ds")
        for t in temp:
            dat.append(t)
        for d in dat:
            assert d is None

        dat = []
        for string in [
            "_Gii",
            "_Gij",
            "_Gji",
            "_Vu1",
            "_Vu2",
        ]:
            temp = parse(dictionary, string)
            for t in temp:
                dat.append(t)
        for d in dat:
            assert d == []

        grogupy.save(builder, "./benchmarks/test_builder_temp2.pkl", compress=3)
        with open("./benchmarks/test_builder_temp2.pkl", "rb") as f:
            dictionary = pickle.load(f)
        dat = []
        temp = parse(dictionary, "_dh")
        for t in temp:
            dat.append(t)
        temp = parse(dictionary, "_ds")
        for t in temp:
            dat.append(t)
        for d in dat:
            assert d is None

        dat = []
        for string in [
            "_Gii",
            "_Gij",
            "_Gji",
            "_Vu1",
            "_Vu2",
        ]:
            temp = parse(dictionary, string)
            for t in temp:
                dat.append(t)
        for d in dat:
            assert d == []

        dat = []
        for string in ["hTRS", "hTRB", "XCF", "H_XCF"]:
            temp = parse(dictionary, string)
            for t in temp:
                dat.append(t)
        for d in dat:
            assert d is None


if __name__ == "__main__":
    pass
