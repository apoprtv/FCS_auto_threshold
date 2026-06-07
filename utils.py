import numpy as np
import seaborn as sns

import matplotlib.pyplot as plt

import plotly.graph_objects as go
from processor import Processor

processor = Processor()


def draw_heatmap(data):
    x_vals = data["x"]
    y_vals = data["y"]
    heatmap, xedges, yedges = np.histogram2d(
        x_vals, y_vals, bins=100, range=[[0, 100], [0, 100]]
    )
    heatmap = heatmap / heatmap.max()

    fig = plt.figure()
    plt.title("dupa")
    hm = sns.heatmap(heatmap.T, cmap="viridis")
    hm.invert_yaxis()

    return fig


def change_category(state):
    pass


def process_data(state):
    if state.file_path:
        fcs, df = processor.load_fcs(state.file_path)
        result = processor.process(fcs, df, config)
        print(result.data.keys())
        print(result.data)
        heatmap = processor.make_heatmap(
            result.data["x"], result.data["y"], config, state.file_path
        )
        state.plotly_fig = go.Figure(data=go.Heatmap(z=heatmap.T, colorscale="Viridis"))
        print("Data processed successfully.")