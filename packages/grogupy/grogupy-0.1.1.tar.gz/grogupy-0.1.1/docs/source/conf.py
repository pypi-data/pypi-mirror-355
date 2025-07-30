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

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))
from grogupy import __sisl__version__, __version__

# Project informations
project = "grogupy"
copyright = "2024-2025, Grogupy Team"
author = "Grogupy"
release = __version__

# Build extensions
extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_tabs.tabs",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxcontrib.bibtex",
    "nbsphinx",
    "sphinx_substitution_extensions",
]

# code block substitution
rst_prolog = f"""
.. |release| replace:: {release}
.. |sisl_version| replace:: {__sisl__version__}
.. |date| replace:: {str(datetime.date.today())}
"""

# Autosummary and autodoc
autosummary_generate = True
autodoc_member_order = "alphabetical"
templates_path = ["_templates"]

# HTML stuff
html_theme = "sphinx_rtd_theme"
html_title = f"grogupy {__version__}"

# for bibliography
bibtex_bibfiles = ["references.bib"]
bibtex_default_style = "plain"
master_doc = "index"
bibtex_encoding = "latin"
bibtex_tooltips = True

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
