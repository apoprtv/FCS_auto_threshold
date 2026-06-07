from taipy.gui import Gui
import taipy.gui.builder as tgb
import numpy as np

import plotly.graph_objects as go
from config import Config

from utils import change_category

config = Config(
    MIN_DIST=0,
    XMAX=250000,
    YMAX=250000,
    BINS=1000,
    SHOW_PLOTS=False,
    SAVE_PLOTS=False,
    VARIANT=0,
)


selected_category = "dupa"
categories = ["dupa", "statki"]
data = {"x_col": [0, 1, 2], "y_col_1": [4, 1, 2], "y_col_2": [3, 1, 2]}

layout = {"yaxis": {"title": "Revenue (USD)"}, "title": "Sales by State"}

heatmap_data = {"x": [10, 20, 30, 30], "y": [50, 60, 90, 90]}

heatmap, xedges, yedges = np.histogram2d(
    heatmap_data.get("x", []),
    heatmap_data.get("y", []),
    bins=100,
    range=[[0, 100], [0, 100]],
)
heatmap = heatmap / heatmap.max()

plotly_fig = go.Figure(data=go.Heatmap(z=heatmap.T, colorscale="Viridis"))

plotly_fig.update_layout(title="Heatmap", width=600, height=600)


### PAGE ###

with tgb.Page() as page:
    file_path = ""

    tgb.selector(
        value="{selected_category}", lov="{categories}", on_change=change_category  # type: ignore
    )

    tgb.chart(
        "{data}",
        x="x_col",
        y__1="y_col_1",
        y__2="y_col_2",
        type__1="bar",
        type__2="bar",
        color__1="blue",
        color__2="red",
    )

    tgb.file_selector(content="{file_path}")

    # tgb.button("Process data", on_action=process_data)

    tgb.chart(figure="{plotly_fig}")

    tgb.table(data="{data}")

    selected_category = "{selected_category}"

    tgb.text(f"This is the selected category: {selected_category}")
    tgb.text("This is the selected category: {selected_category}")

if __name__ == "__main__":
    Gui(page=page).run(title="duppa", dark_mode=True, debug=True, watermark="")
