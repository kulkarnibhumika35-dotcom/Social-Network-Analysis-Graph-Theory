"""
Visualization Module

Handles rendering and plotting network graphs using NetworkX and Matplotlib.
Highlights most-connected individuals, regular connected members, and isolated members.
"""

from typing import List, Optional, Set, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import networkx as nx


def plot_network(
    graph: nx.Graph,
    figsize: Tuple[int, int] = (10, 7),
    title: Optional[str] = "Social Network Structure",
    node_size: int = 1800,
) -> plt.Figure:
    """
    Draw the social network graph using NetworkX and Matplotlib.

    - People are rendered as nodes with clear text labels.
    - Friendships are rendered as undirected edges.
    - Most-connected person(s) are highlighted in Amber/Gold.
    - Isolated users (degree 0) are highlighted in Red/Coral.
    - Other connected members are displayed in Blue.
    - Empty networks are handled gracefully with a clean placeholder canvas.

    Parameters:
        graph: NetworkX undirected graph.
        figsize: Figure dimensions (width, height) in inches.
        title: Plot title.
        node_size: Visual diameter of nodes.

    Returns:
        plt.Figure: The rendered Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFAFA")

    num_nodes = graph.number_of_nodes()

    # Handle empty network safely
    if num_nodes == 0:
        ax.text(
            0.5,
            0.5,
            "Network is Empty\n\nAdd members and friendships in 'Manage Network'\nto view the graph visualization.",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=13,
            color="#64748B",
            transform=ax.transAxes,
            bbox=dict(
                boxstyle="round,pad=1.0",
                facecolor="#F1F5F9",
                edgecolor="#CBD5E1",
                linewidth=1.5,
            ),
        )
        ax.axis("off")
        if title:
            ax.set_title(title, fontsize=15, fontweight="bold", pad=15, color="#1E293B")
        fig.tight_layout()
        return fig

    # Compute node categories
    degrees = dict(graph.degree())
    max_deg = max(degrees.values()) if degrees else 0

    isolates: Set[str] = set(nx.isolates(graph))
    most_connected: Set[str] = (
        {node for node, deg in degrees.items() if deg == max_deg}
        if max_deg > 0
        else set()
    )

    # Assign distinct colors per category
    # Amber/Gold: Most-connected, Red: Isolated, Blue: Standard connected
    COLOR_CONNECTED = "#3B82F6"
    COLOR_MOST_CONNECTED = "#F59E0B"
    COLOR_ISOLATED = "#EF4444"

    node_colors: List[str] = []
    for node in graph.nodes():
        if node in isolates:
            node_colors.append(COLOR_ISOLATED)
        elif node in most_connected:
            node_colors.append(COLOR_MOST_CONNECTED)
        else:
            node_colors.append(COLOR_CONNECTED)

    # Layout calculation
    # Using spring layout with fixed seed for visual consistency across reruns
    pos = nx.spring_layout(graph, seed=42, k=1.0 / (num_nodes**0.5 + 0.1))

    # 1. Draw edges
    if graph.number_of_edges() > 0:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edge_color="#94A3B8",
            width=2.0,
            alpha=0.75,
        )

    # 2. Draw nodes
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=node_size,
        edgecolors="#0F172A",
        linewidths=1.8,
    )

    # 3. Draw labels
    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=10,
        font_weight="bold",
        font_family="sans-serif",
        font_color="#0F172A",
    )

    # 4. Construct descriptive Legend
    legend_handles = []
    if most_connected:
        legend_handles.append(
            mlines.Line2D(
                [],
                [],
                color="none",
                marker="o",
                markersize=11,
                markerfacecolor=COLOR_MOST_CONNECTED,
                markeredgecolor="#0F172A",
                label=f"Most Connected (deg {max_deg})",
            )
        )
    if any(node not in isolates and node not in most_connected for node in graph.nodes()):
        legend_handles.append(
            mlines.Line2D(
                [],
                [],
                color="none",
                marker="o",
                markersize=11,
                markerfacecolor=COLOR_CONNECTED,
                markeredgecolor="#0F172A",
                label="Connected Member",
            )
        )
    if isolates:
        legend_handles.append(
            mlines.Line2D(
                [],
                [],
                color="none",
                marker="o",
                markersize=11,
                markerfacecolor=COLOR_ISOLATED,
                markeredgecolor="#0F172A",
                label="Isolated Member (deg 0)",
            )
        )
    if graph.number_of_edges() > 0:
        legend_handles.append(
            mlines.Line2D(
                [],
                [],
                color="#94A3B8",
                lw=2.0,
                label="Friendship",
            )
        )

    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="upper right",
            frameon=True,
            facecolor="#F8FAFC",
            edgecolor="#CBD5E1",
            fontsize=9,
            title="Legend",
            title_fontsize=10,
        )

    if title:
        ax.set_title(title, fontsize=15, fontweight="bold", pad=15, color="#1E293B")

    ax.axis("off")
    fig.tight_layout()
    return fig
