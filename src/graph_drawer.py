import numpy as np
import plotly.graph_objects as go

from config import Config


def create_heatmap(
    x_vals, y_vals, config: Config, filename: str, name: str
) -> go.Figure:
    """
    Creates a heatmap based on the provided x and y values.
    """
    heatmap, xedges, yedges = np.histogram2d(
        x_vals, y_vals, bins=config.BINS, range=[[0, config.XMAX], [0, config.YMAX]]
    )
    heatmap = heatmap / heatmap.max()

    fig = go.Figure(
        data=go.Heatmap(
            heatmap.T,
            origin="lower",
            labels={"x": "FSC-A", "y": "SSC-A", "color": "Density"},
            title=f"{name} Heatmap",
        )
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
