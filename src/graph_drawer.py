import numpy as np
import plotly.graph_objects as go
from dataclasses import dataclass
import pandas as pd
from typing import Any

from config import Config


@dataclass()
class GraphData:
    channel_names: list[str]
    x_vals_original: pd.Series | np.ndarray
    y_vals_original: pd.Series | np.ndarray
    x_vals: pd.Series | np.ndarray
    y_vals: pd.Series | np.ndarray
    x_smooth: np.ndarray
    y_smooth: np.ndarray | tuple
    mask: Any | None


def create_heatmap(
    graph_data: GraphData, config: Config, show_points: bool, name: str | None
) -> go.Figure:
    """
    Creates a heatmap based on the provided x and y values.
    """
    if not name:
        name = ""

    y_smooth = graph_data.y_smooth

    if type(y_smooth) is not np.ndarray:
        y_smooth = np.ndarray(y_smooth)

    heatmap, xedges, yedges = np.histogram2d(
        graph_data.x_vals,
        graph_data.y_vals,
        bins=config.BINS,
        range=[
            [0, max(graph_data.x_vals_original.max(), graph_data.x_smooth.max())],
            [
                0,
                max(
                    graph_data.y_vals_original.max(),
                    y_smooth.max(),
                ),
            ],
        ],
    )
    heatmap = heatmap / heatmap.max()

    x_centers = (xedges[:-1] + xedges[1:]) / 2
    y_centers = (yedges[:-1] + yedges[1:]) / 2

    fig_data: list[Any] = [
        go.Heatmap(
            z=heatmap.T, x=x_centers, y=y_centers, colorscale="Viridis", showscale=False
        ),
    ]

    if show_points:
        fig_data.append(
            go.Scatter(
                x=graph_data.x_vals,
                y=graph_data.y_vals,
                mode="markers",
                marker=dict(
                    size=1,
                    color="white",
                    opacity=0.4,
                ),
                name="points",
            )
        )

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
        uirevision="constant",
    )

    return fig
