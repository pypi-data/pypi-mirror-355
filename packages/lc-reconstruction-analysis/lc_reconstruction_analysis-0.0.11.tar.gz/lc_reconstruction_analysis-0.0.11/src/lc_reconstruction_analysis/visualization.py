"""
    Plotting tools for looking at cell structure
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d  # noqa: F401
import lc_reconstruction_analysis.utils as utils


def plot_cells(dataDF, graphs, ax=None, **kwargs):
    """
    Plot morphology of cells
    dataDF, dataframe of cells
    graphs, graphs of tcells
    """
    if ax is None:
        ax = plt.figure().add_subplot(projection="3d")
    for name in dataDF["Graph"].values:
        ax = plot_cell(graphs[name], ax=ax, **kwargs)
    return ax


def plot_cell(
    graph,
    ax=None,
    plot_list=["soma", "axon", "dendrites"],
    color=None,
    **kwargs,
):
    """
    Plot morphology of cell
    graph, graph of cells
    plot_list, which structures to plot
    """

    soma = utils.get_subgraph(graph, "structure_id", [1])
    dendrites = utils.get_subgraph(graph, "structure_id", [3])
    axon = utils.get_subgraph(graph, "structure_id", [2])
    center = soma.nodes[1]["pos"]

    if ax is None:
        ax = plt.figure().add_subplot(projection="3d")
    if "dendrites" in plot_list:
        plot_subgraph(
            dendrites, color or "mediumblue", ax, plot_list=["edges"], **kwargs
        )
    if "axon" in plot_list:
        plot_subgraph(
            axon,
            color or "orange",
            ax,
            plot_list=["edges"],
            center=center,
            **kwargs,
        )
    if "soma" in plot_list:
        plot_subgraph(soma, "magenta", ax, plot_list=["nodes"], **kwargs)
        for u, v in graph.edges:
            if u == 1 or v == 1:
                pos1 = graph.nodes[u]["pos"]
                pos2 = graph.nodes[v]["pos"]
                ax.plot(
                    [pos1[0], pos2[0]],
                    [pos1[1], pos2[1]],
                    [pos1[2], pos2[2]],
                    "-",
                    color=color or "magenta",
                    alpha=kwargs.get("alpha", 1),
                )
    ax.set_xlabel("AP", fontsize=12)
    ax.set_ylabel("DV", fontsize=12)
    ax.set_zlabel("ML", fontsize=12)
    return ax


def plot_subgraph(
    graph,
    color,
    ax,
    plot_list=["nodes", "edges"],
    max_radius=None,
    center=None,
    alpha=1,
    max_length=None,
    **kwargs,
):
    """
    Plot just a subgraph
    """
    if (max_radius is not None) and (max_length is not None):
        raise Exception("max_radius and max_length should not both be set")
    if "nodes" in plot_list:
        for node in graph.nodes:
            pos = graph.nodes[node]["pos"]
            ax.plot(pos[0], pos[1], pos[2], "o", color=color, alpha=alpha / 2)
    if "edges" in plot_list:
        for u, v in graph.edges:
            if max_radius is not None:
                pos_u = np.array(graph.nodes[u]["pos"])
                dist_u = np.linalg.norm(pos_u - center)
                pos_v = np.array(graph.nodes[v]["pos"])
                dist_v = np.linalg.norm(pos_v - center)
                if (dist_u > max_radius) or (dist_v > max_radius):
                    continue
            elif max_length is not None:
                if (graph.nodes[u]["wire_length"] > max_length) or (
                    graph.nodes[v]["wire_length"] > max_length
                ):
                    continue
            pos1 = graph.nodes[u]["pos"]
            pos2 = graph.nodes[v]["pos"]
            ax.plot(
                [pos1[0], pos2[0]],
                [pos1[1], pos2[1]],
                [pos1[2], pos2[2]],
                "-",
                color=color,
                alpha=alpha,
            )
