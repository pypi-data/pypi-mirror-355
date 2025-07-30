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

from typing import TYPE_CHECKING, Union

import numpy as np
import plotly.graph_objs as go
import sisl

from grogupy.io import load_Builder
from grogupy.physics import (
    Builder,
    Contour,
    Kspace,
    MagneticEntity,
    MagneticEntityList,
    Pair,
    PairList,
)


def plot_contour(contour: Contour, **kwargs) -> go.Figure:
    """Creates a plot from the contour sample points.

    If there are too many eigenvalues, then they are subsamled
    them for the plot.

    Parameters
    ----------
    contour : Contour
        Contour class that contains the energy samples and weights

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # Create the scatter plot
    trace = go.Scatter(x=contour.samples.real, y=contour.samples.imag, mode="markers")

    # if the eigenvalues are available
    if contour.automatic_emin:
        # convert the path to the EIG file
        eigfile = contour._eigfile
        if eigfile.endswith("fdf"):
            eigfile = eigfile[:-3] + "EIG"

        # try to use the path to the EIG file...
        try:
            # read eigenvals
            eigs = sisl.get_sile(eigfile).read_data().flatten()
            eigs.sort()
            # if there are too many eigenvalues subsample them for plot
            if len(eigs) > 10000:
                eigs = eigs[:: int(len(eigs) / 10000)]
                # traces to eigenvals
                eig_trace1 = go.Scatter(
                    x=eigs[eigs < 0],
                    y=np.zeros_like(eigs[eigs < 0]),
                    mode="markers",
                    name="Subsampled occupied DFT eigs",
                )
                eig_trace2 = go.Scatter(
                    x=eigs[0 < eigs],
                    y=np.zeros_like(eigs[0 < eigs]),
                    mode="markers",
                    name="Subsampled unoccupied DFT eigs",
                )
            else:
                eig_trace1 = go.Scatter(
                    x=eigs[eigs < 0],
                    y=np.zeros_like(eigs[eigs < 0]),
                    mode="markers",
                    name="Occupied DFT eigs",
                )
                eig_trace2 = go.Scatter(
                    x=eigs[0 < eigs],
                    y=np.zeros_like(eigs[0 < eigs]),
                    mode="markers",
                    name="Unoccupied DFT eigs",
                )
            fig = go.Figure(data=[trace, eig_trace1, eig_trace2])
        # but something might have been moved, in which case just do the regular plot
        except:
            fig = go.Figure(data=trace)

    # else just plot the contour
    else:
        fig = go.Figure(data=trace)

    # Update the layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        title="Energy contour integral",
        xaxis_title="Real axis [eV]",
        yaxis_title="Imaginary axis [eV]",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
        legend=dict(
            x=1,
            y=1,
            xanchor="right",
        ),
    )

    return fig


def plot_kspace(kspace: Kspace, **kwargs) -> go.Figure:
    """Creates a plot from the Brillouin zone sample points.

    Parameters
    ----------
    kspace : Kspace
        Kspace class that contains the Brillouin-zone samples and weights

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # Create the scatter plot
    # Create 3D scatter plot
    trace = go.Scatter3d(
        name=f"Kpoints",
        x=kspace.kpoints[:, 0],
        y=kspace.kpoints[:, 1],
        z=kspace.kpoints[:, 2],
        mode="markers",
        marker=dict(
            size=5,
            color=kspace.weights,
            colorscale="Viridis",
            opacity=1,
            colorbar=dict(title="Weights of kpoints", x=0.75),
        ),
    )

    # Update the layout

    layout = go.Layout(
        autosize=False,
        title="Brillouin zone sampling",
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        scene=dict(
            aspectmode="data",
            xaxis=dict(title="X Axis", showgrid=True, gridwidth=1),
            yaxis=dict(title="Y Axis", showgrid=True, gridwidth=1),
            zaxis=dict(title="Z Axis", showgrid=True, gridwidth=1),
        ),
    )

    # Create figure and show
    fig = go.Figure(data=[trace], layout=layout)

    return fig


def plot_magnetic_entities(
    magnetic_entities: Union[Builder, list[MagneticEntity], MagneticEntityList],
    **kwargs,
) -> go.Figure:
    """Creates a plot from a list of magnetic entities.

    Parameters
    ----------
    magnetic_entities : Union[Builder, list[MagneticEntity], MagneticEntityList]
        The magnetic entities that contain the tags and coordinates

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # conversion line for the case when it is set as the plot function of a builder
    if isinstance(magnetic_entities, Builder):
        magnetic_entities = magnetic_entities.magnetic_entities
    elif not (
        isinstance(magnetic_entities, list)
        or isinstance(magnetic_entities, MagneticEntityList)
    ):
        magnetic_entities = [magnetic_entities]

    tags = [m.tag for m in magnetic_entities]
    coords = [m._xyz for m in magnetic_entities]

    colors = ["red", "green", "blue", "purple", "orange", "cyan", "magenta"]
    colors = colors * (len(coords) // len(colors) + 1)

    # Create figure
    fig = go.Figure()
    for coord, color, tag in zip(coords, colors, tags):
        fig.add_trace(
            go.Scatter3d(
                name=tag,
                x=coord[:, 0],
                y=coord[:, 1],
                z=coord[:, 2],
                mode="markers",
                marker=dict(size=10, opacity=0.8, color=color),
            )
        )

    # Create layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        scene=dict(
            aspectmode="data",
            xaxis=dict(title="X Axis", showgrid=True, gridwidth=1),
            yaxis=dict(title="Y Axis", showgrid=True, gridwidth=1),
            zaxis=dict(title="Z Axis", showgrid=True, gridwidth=1),
        ),
    )

    return fig


def plot_pairs(
    pairs: Union[Builder, list[Pair], PairList],
    connect: bool = False,
    cell: bool = True,
    **kwargs,
) -> go.Figure:
    """Creates a plot from a list of pairs.

    Parameters
    ----------
    pairs : Union[Builder, list[Pair], PairList]
        The pairs that contain the tags and coordinates
    connect : bool, optional
        Wether to connect the pairs or not, by default False
    cell: bool, optional
        Wether to show the unit cell, by default True

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # conversion line for the case when it is set as the plot function of a builder
    if isinstance(pairs, Builder):
        pairs = pairs.pairs
    elif not (isinstance(pairs, list) or isinstance(pairs, PairList)):
        pairs = [pairs]

    # the centers can contain many atoms
    centers = [p.xyz[0] for p in pairs]

    # find unique centers
    uniques = []

    def in_unique(c):
        for u in uniques:
            if c.shape == u.shape:
                if np.all(c == u):
                    return True
        return False

    for c in centers:
        if not in_unique(c):
            uniques.append(c)
    # findex indexes for the same center
    idx = [[] for u in uniques]
    for i, u in enumerate(uniques):
        for j, c in enumerate(centers):
            if c.shape == u.shape:
                if np.all(c == u):
                    idx[i].append(j)

    center_tags = np.array([p.tags[0] for p in pairs])

    interacting_atoms = np.array([p.xyz[1] for p in pairs], dtype=object)
    interacting_tags = np.array(
        [p.tags[1] + ", ruc:" + str(p.supercell_shift) for p in pairs]
    )

    colors = ["red", "green", "blue", "purple", "orange", "cyan", "magenta"]
    colors = colors * (len(centers) // len(colors) + 1)

    # Create figure
    fig = go.Figure()
    for i in range(len(idx)):
        center = centers[idx[i][0]]
        center_tag = center_tags[idx[i][0]]
        color = colors[i]
        # Create 3D scatter plot
        fig.add_trace(
            go.Scatter3d(
                name="Center:" + center_tag,
                x=center[:, 0],
                y=center[:, 1],
                z=center[:, 2],
                mode="markers",
                marker=dict(size=10, opacity=0.8, color=color),
            )
        )
        for interacting_atom, interacting_tag in zip(
            interacting_atoms[idx[i]], interacting_tags[idx[i]]
        ):
            legend_group = f"pair {center_tag}-{interacting_atom}"
            fig.add_trace(
                go.Scatter3d(
                    name=interacting_tag,
                    x=interacting_atom[:, 0],
                    y=interacting_atom[:, 1],
                    z=interacting_atom[:, 2],
                    legendgroup=legend_group,
                    mode="markers",
                    marker=dict(size=5, opacity=0.5, color=color),
                )
            )
            if connect:
                fig.add_trace(
                    go.Scatter3d(
                        x=[center.mean(axis=0)[0], interacting_atom.mean(axis=0)[0]],
                        y=[center.mean(axis=0)[1], interacting_atom.mean(axis=0)[1]],
                        z=[center.mean(axis=0)[2], interacting_atom.mean(axis=0)[2]],
                        mode="lines",
                        legendgroup=legend_group,
                        showlegend=False,
                        line=dict(color=color),
                    )
                )

    # add unit cell to the plot
    if cell:
        x = pairs[0].cell[0, :]
        y = pairs[0].cell[1, :]
        z = pairs[0].cell[2, :]
        vecs0 = np.array(
            [
                np.zeros(3),
                np.zeros(3),
                np.zeros(3),
                x,
                x,
                y,
                y,
                z,
                z,
                x + y + z,
                x + y + z,
                x + y + z,
            ]
        )
        vecs1 = np.array(
            [x, y, z, x + y, x + z, y + x, y + z, z + x, z + y, x + y, x + z, y + z]
        )
        for v1, v2 in zip(vecs0, vecs1):
            fig.add_trace(
                go.Scatter3d(
                    x=[v1[0], v2[0]],
                    y=[v1[1], v2[1]],
                    z=[v1[2], v2[2]],
                    mode="lines",
                    showlegend=False,
                    line=dict(color="black", width=1),
                )
            )

    # Create layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        scene=dict(
            aspectmode="data",
            xaxis=dict(title="X Axis", showgrid=True, gridwidth=1),
            yaxis=dict(title="Y Axis", showgrid=True, gridwidth=1),
            zaxis=dict(title="Z Axis", showgrid=True, gridwidth=1),
        ),
    )

    return fig


def plot_DMI(
    pairs: Union[Builder, list[Pair], PairList], rescale: float = 1, **kwargs
) -> go.Figure:
    """Creates a plot of the DM vectors from a list of pairs.

    It can only use pairs from a finished simulation. The magnitude of
    the vectors are in meV.

    Parameters
    ----------
    pairs : Union[Builder, list[Pair], PairList]
        The pairs that contain the tags, coordinates and the DM vectors
    rescale : float, optional
        The length of the vectors are rescaled by this, by default 1

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # conversion line for the case when it is set as the plot function of a builder
    if isinstance(pairs, Builder):
        pairs = pairs.pairs
    elif not (isinstance(pairs, list) or isinstance(pairs, PairList)):
        pairs = [pairs]

    # Define some example vectors
    vectors = np.array([p.D_meV * rescale for p in pairs])
    # Define origins (optional)
    origins = np.array(
        [(p.M1.xyz_center + p.M2.xyz_center + p.supercell_shift_xyz) / 2 for p in pairs]
    )

    n_vectors = len(vectors)

    labels = ["-->".join(p.tags) + ", ruc:" + str(p.supercell_shift) for p in pairs]

    colors = ["red", "green", "blue", "purple", "orange", "cyan", "magenta"]
    colors = colors * (n_vectors // len(colors) + 1)

    # Create figure
    fig = go.Figure()

    # Maximum vector magnitude for scaling
    max_magnitude = max(np.linalg.norm(v) for v in vectors)

    # Add each vector as a cone
    for i, (vector, origin, label, color) in enumerate(
        zip(vectors, origins, labels, colors)
    ):
        # End point of the vector
        end = origin + vector

        legend_group = f"vector_{i}"

        # Add a line for the vector
        fig.add_trace(
            go.Scatter3d(
                x=[origin[0], end[0]],
                y=[origin[1], end[1]],
                z=[origin[2], end[2]],
                mode="lines",
                line=dict(color=color, width=5),
                name=label,
                legendgroup=legend_group,
                showlegend=True,
            )
        )

        # Add a cone at the end to represent the arrow head
        u, v, w = vector
        fig.add_trace(
            go.Cone(
                x=[end[0]],
                y=[end[1]],
                z=[end[2]],
                u=[u / 5],  # Scale down for better visualization
                v=[v / 5],
                w=[w / 5],
                colorscale=[[0, color], [1, color]],
                showscale=False,
                sizemode="absolute",
                sizeref=max_magnitude / 10,
                legendgroup=legend_group,
                showlegend=False,
            )
        )

    # Set layout properties

    # Create layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        scene=dict(
            aspectmode="data",
            xaxis=dict(title="X Axis", showgrid=True, gridwidth=1),
            yaxis=dict(title="Y Axis", showgrid=True, gridwidth=1),
            zaxis=dict(title="Z Axis", showgrid=True, gridwidth=1),
        ),
    )

    return fig


def plot_Jiso_distance(
    pairs: Union[Builder, list[Pair], PairList], **kwargs
) -> go.Figure:
    """Plots the isotropic exchange as a function of distance.

    Parameters
    ----------
    pairs : Union[Builder, list[Pair], PairList]
        The pairs that contain the exchange and positions

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # conversion line for the case when it is set as the plot function of a builder
    if isinstance(pairs, Builder):
        pairs = pairs.pairs
    elif not (isinstance(pairs, list) or isinstance(pairs, PairList)):
        pairs = [pairs]

    # Create figure
    fig = go.Figure(
        data=go.Scatter(
            x=[p.distance for p in pairs],
            y=[p.J_iso_meV for p in pairs],
            mode="markers",
        )
    )

    # Update the layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        title=f"Isotropic exchange",
        xaxis_title="Pair distance [Ang]",
        yaxis_title="Isotropic exchange [meV]",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
    )

    return fig


def plot_DM_distance(
    pairs: Union[Builder, list[Pair], PairList], **kwargs
) -> go.Figure:
    """Plots the magnitude of DM vectors as a function of distance.

    Parameters
    ----------
    pairs : Union[Builder, list[Pair], PairList]
        The pairs that contain the DM vectors and positions

    Returns
    -------
    plotly.graph_objs.go.Figure
        The created figure
    """

    # conversion line for the case when it is set as the plot function of a builder
    if isinstance(pairs, Builder):
        pairs = pairs.pairs
    elif not (isinstance(pairs, list) or isinstance(pairs, PairList)):
        pairs = [pairs]

    # Create figure
    fig = go.Figure(
        data=go.Scatter(
            x=[p.distance for p in pairs],
            y=np.linalg.norm([p.D_meV for p in pairs], axis=1),
            mode="markers",
        )
    )

    # Update the layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        title=f"Norm of the DM vectors",
        xaxis_title="Pair distance [Ang]",
        yaxis_title="DM norm [meV]",
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
        ),
    )

    return fig


def plot_1D_convergence(
    files: Union[str, list[str]],
    parameter: str,
    maxdiff: float = 1e-4,
    method: str = "absolute",
    **kwargs,
) -> go.Figure:
    """Reads output files and create a plot for the convergence test.

    Parameters
    ----------
    files : Union[str, list[str]]
        The path to the output files .pkl
    parameter : {"eset", "esetp", "kset"}
        The parameter for the test
    maxdiff : float, optional
        The criteria for the convergence by relative difference from the last step, by default 1e-4
    method: str, optional
        The convergence method, can be 'relative' or 'absolute', by default 'absolute'

    Returns
    -------
    go.Figure
        Plotly figure

    Raises
    ------
    Exception
        Multiple parameters changed in different runs!
    Exception
        Unknown convergence parameter!
    """
    # standardize input
    parameter = parameter.lower()

    # load
    if not isinstance(files, list):
        files = [files]
    builders = []
    spin_models = []
    for f in files:
        builders.append(load_Builder(f))
        spin_models.append(builders[-1].spin_model)
    builders = np.array(builders, dtype=object)

    # check spin models
    spin_models = np.unique(np.array(spin_models))
    if len(spin_models) != 1:
        raise Exception(f"Multiple spin models in files: {spin_models}!")

    # sort
    conv_params = []
    for b in builders:
        if parameter == "eset":
            if not (
                b.kspace == builders[0].kspace
                and b.contour.esetp == builders[0].contour.esetp
            ):
                raise Exception("Multiple parameters changed in different runs!")
            conv_params.append(b.contour.eset)
        elif parameter == "esetp":
            if not (
                b.kspace == builders[0].kspace
                and b.contour.eset == builders[0].contour.eset
            ):
                raise Exception("Multiple parameters changed in different runs!")
            conv_params.append(b.contour.esetp)
        elif parameter == "kset":
            if not (b.contour == builders[0].contour):
                raise Exception("Multiple parameters changed in different runs!")
            conv_params.append(b.kspace.NK)
        else:
            raise Exception(
                f"Unknown convergence parameter: {parameter}! Use: eset, esetp or kset"
            )
    conv_params = np.array(conv_params)
    idx = np.argsort(conv_params)
    conv_params = conv_params[idx]
    builders = builders[idx]

    # get all data
    compare = []
    for b in builders:
        dat = []
        if spin_models[0] != "isotropic-only":
            for m in b.magnetic_entities:
                dat.append(m.K_meV)
            for p in b.pairs:
                dat.append(p.J_meV)
        else:
            for p in b.pairs:
                dat.append(p.J_iso_meV)
        compare.append(np.array(dat).flatten())
    compare = np.array(compare).T

    # add lines
    fig = go.Figure()
    for i in range(len(compare)):
        fig.add_trace(
            go.Scatter(
                x=conv_params, y=compare[i], mode="markers+lines", showlegend=False
            )
        )

    # find maxdiff point
    if method[0].lower() == "r":
        idx = np.argwhere(
            abs(np.diff(compare, axis=1) / compare[:, :-1]).max(axis=0) < maxdiff
        )
    elif method[0].lower() == "a":
        idx = np.argwhere(abs(np.diff(compare, axis=1)).max(axis=0) < maxdiff)
    else:
        raise Exception(f"Unknown convergence method: {method}")

    if len(idx) != 0:
        idx = idx.min()
        fig.add_vline(
            x=(conv_params[idx] + conv_params[idx + 1]) / 2,
            line_width=1,
            line_color="red",
            name="Reached convergence criteria: %0.3e" % maxdiff,
            showlegend=True,
        )

    # a little renaming for kset
    if parameter == "kset":
        parameter = "total number of k points"

    # Update the layout
    fig.update_layout(
        autosize=False,
        width=kwargs.get("width", 800),
        height=kwargs.get("height", 500),
        title=f"Convergence on {parameter}",
        xaxis_title=f"{parameter.capitalize()} [ ]",
        yaxis_title="System vector [meV]",
        xaxis=dict(
            tickmode="array",
            tickvals=conv_params,
            ticktext=[str(i) for i in conv_params],
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            type="log",
            tickformat="0.2e",
            showgrid=True,
            gridwidth=1,
        ),
        legend=dict(
            x=1,
            y=1,
            xanchor="right",
        ),
    )

    return fig


if __name__ == "__main__":
    pass
