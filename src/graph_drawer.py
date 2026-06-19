import numpy as np
import plotly.graph_objects as go
from dataclasses import dataclass
import pandas as pd
import numpy as np
from typing import Any

from config import Config


@dataclass(frozen=True)
class GraphData:
    channel_names: list[str]
    x_vals_original: pd.Series | np.ndarray
    y_vals_original: pd.Series | np.ndarray
    x_vals: pd.Series | np.ndarray
    y_vals: pd.Series | np.ndarray
    x_smooth: np.ndarray | None
    y_smooth: np.ndarray | tuple | None
    mask: Any | None


def create_heatmap(
    graph_data: GraphData, config: Config, name: str | None
) -> go.Figure:
    """
    Creates a heatmap based on the provided x and y values.
    """
    if not name:
        name = ""

    heatmap, xedges, yedges = np.histogram2d(
        graph_data.x_vals,
        graph_data.y_vals,
        bins=config.BINS,
        range=[[0, config.XMAX], [0, config.YMAX]],
    )
    heatmap = heatmap / heatmap.max()

    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2

    fig_data: list[Any] = [
        go.Heatmap(z=heatmap.T, x=x_centers, y=y_centers, colorscale="Viridis"),
        go.Scattergl(
            x=graph_data.x_vals,
            y=graph_data.y_vals,
            mode="markers",
            marker=dict(
                size=2,
                color="white",
                opacity=0.3,
            ),
            name="points",
        ),
    ]

    if graph_data.x_smooth is not None and graph_data.y_smooth is not None:
        fig_data.append(
            go.Scatter(
                x=graph_data.x_smooth,
                y=graph_data.y_smooth,
                mode="lines",
                line=dict(color="red", width=1),
                opacity=0.3,
                name="Smoothed",
            )
        )

    fig = go.Figure(data=fig_data)

    fig.update_layout(
        width=600,
        height=600,
        xaxis=dict(range=[0, config.XMAX]),
        yaxis=dict(range=[0, config.YMAX]),
        transition=dict(duration=500, easing="cubic-in-out"),
    )

    return fig


def update_heatmap(fig, graph_data, config) -> go.Figure:
    heatmap, xedges, yedges = np.histogram2d(
        graph_data.x_vals,
        graph_data.y_vals,
        bins=config.BINS,
        range=[[0, config.XMAX], [0, config.YMAX]],
    )

    heatmap = heatmap / heatmap.max()

    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2

    fig.data[0].z = heatmap.T
    fig.data[0].x = x_centers
    fig.data[0].y = y_centers

    fig.data[1].marker.size = np.where(
        graph_data.mask,
        8,
        2,
    )

    return fig


# LEGACY

# def create_heatmap_plot(
#     x_vals,
#     y_vals,
#     filename: str,
#     name: str,
#     heatmap: np.ndarray,
#     config: Config,
# ):
#     plt.figure()
#     plt.title(f"{name}")
#     hm = sns_heatmap(heatmap.T, cmap="viridis")
#     hm.invert_yaxis()

#     if config.SHOW_PLOTS:
#         plt.show()

#     if config.SAVE_PLOTS:
#         plt.savefig(f"{filename}_{name}_heatmap.png")
