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
from grogupy.viz import plot_1D_convergence


def main():
    """Main entry point of the script."""

    # setup parser
    parser = argparse.ArgumentParser(
        description="Load results from multiple .pkl files and do convergence analysis with them."
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="type",
        default=None,
        help="Type of convergence test, can be 'eset', 'esetp' or 'kset'.",
    )
    parser.add_argument(
        "-f",
        "--files",
        default=None,
        dest="files",
        help="Path to the files taking part in the convergence tests.",
    )
    parser.add_argument(
        "-m",
        "--maxdiff",
        dest="maxdiff",
        default=1e-4,
        help="The criteria for the convergence by maximum difference from the last step, by default 1e-4.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="Output file name.",
    )
    parser.add_argument(
        "-c" "--cite",
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
        if args.files is None or args.type is None:
            return

    # check if we have correct input
    if args.files is None or args.type is None:
        raise Exception("Convergence type and input files are needed!")

    # get the output name
    if args.output is None:
        name = f"grogupy_{args.type}_convergence.html"
    else:
        name = args.output
        if not name.endswith(".html"):
            name += ".html"

    # get files
    files = list(set(args.files.replace("'", "").split()))
    if len(files) < 2:
        raise Exception("Not enough files for convergence test!")

    with open(name, "w") as file:
        file.write(r"Files taking part in test: <br>")
        file.write(r"<br>".join(files))

        fig = plot_1D_convergence(files, args.type, args.maxdiff)
        file.write(fig.to_html(full_html=False, include_plotlyjs=True))

    print(f"The output file is: {name}")
    print(__definitely_not_grogu__)


if __name__ == "__main__":
    main()
