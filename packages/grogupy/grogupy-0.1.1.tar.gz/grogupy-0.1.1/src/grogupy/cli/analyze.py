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

import argparse

from grogupy import __citation__, __definitely_not_grogu__
from grogupy.io import load_Builder
from grogupy.viz import (
    plot_contour,
    plot_DM_distance,
    plot_DMI,
    plot_Jiso_distance,
    plot_kspace,
    plot_magnetic_entities,
    plot_pairs,
)


def main():
    """Main entry point of the script."""

    # setup parser
    parser = argparse.ArgumentParser(
        description="Load results from a .pkl file and do a summary on the system."
    )
    parser.add_argument(
        "file", nargs="?", help="Path to a .pkl file containing the results."
    )
    parser.add_argument(
        "-c",
        "--cite",
        dest="cite",
        action="store_true",
        default=False,
        help="Print the citation of the package.",
    )
    # parameters from command line
    args = parser.parse_args()

    # print citation if needed
    if args.cite:
        print(__citation__ + __definitely_not_grogu__)
        if args.file is None:
            return

    # Reading input
    system = load_Builder(args.file)

    # get the output name
    name = args.file
    if name.endswith(".pkl"):
        name = name[:-4]
    name += ".analysis.html"

    with open(name, "w") as file:
        file.write(
            system.to_magnopy()
            .replace("\n", "<br>\n")
            .replace(" ", "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;")
        )
        fig = plot_contour(system.contour)
        file.write(fig.to_html(full_html=False, include_plotlyjs=True))

        fig = plot_kspace(system.kspace)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

        fig = plot_Jiso_distance(system)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

        fig = plot_DM_distance(system)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

        fig = plot_magnetic_entities(system)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

        fig = plot_pairs(system)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

        fig = plot_DMI(system).add_traces(plot_pairs(system, connect=True).data)
        file.write(fig.to_html(full_html=False, include_plotlyjs=False))

    print(f"The output file is: {name}")
    print(__definitely_not_grogu__)


if __name__ == "__main__":
    main()
