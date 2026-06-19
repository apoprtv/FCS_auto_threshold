from taipy.gui import Gui
from taipy.gui.state import State
import taipy.gui.builder as tgb
import numpy as np
import plotly.graph_objects as go
from config import Config
import processor
from graph_drawer import create_heatmap, update_heatmap, GraphData

config = Config(
    MIN_DIST=0,
    XMAX=250000,
    YMAX=250000,
    BINS=1000,
    SHOW_PLOTS=False,
    SAVE_PLOTS=False,
    VARIANT="Above",
)


def set_show_plots(state, value):
    state.config.SHOW_PLOTS = value


selected_category = "dupa"
categories = ["dupa", "statki"]
show_plots_lov = [True, False]
variants = ["Above", "Below", "Both"]

min_dist = 0
xmax = 250000
ymax = 250000
variant = "Above"
show_plots = False

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

### ===========

file_path = ""
graph_left = None
graph_right = None

plotly_fig = go.Figure(data=go.Heatmap(z=heatmap.T, colorscale="Viridis"))
plotly_fig.update_layout(title="Heatmap", width=600, height=600)


def load_file(state: State) -> GraphData:
    print(f"action!, this is file_path: {state.file_path}")
    channel_names, unprocessed_data = processor.load_fcs(state.file_path)
    x_vals, y_vals = processor.extract_data(unprocessed_data)
    x_smooth, y_smooth = processor.fit_curve(x_vals, y_vals)
    return GraphData(
        channel_names, x_vals, y_vals, x_vals, y_vals, x_smooth, y_smooth, None
    )


def update_graph(state: State, graph_name: str, graph_data: GraphData):
    if not hasattr(state, graph_name):
        raise ValueError(f"Unidentified graph_name: {graph_name}")

    updated_config = Config(
        MIN_DIST=state.min_dist,
        XMAX=state.xmax,
        YMAX=state.ymax,
        VARIANT=state.variant,
        SHOW_PLOTS=state.show_plots,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    graph = getattr(state, graph_name, None)

    if graph is None:
        graph = create_heatmap(graph_data, updated_config, state.file_path)
    else:
        graph = update_heatmap(graph, graph_data, updated_config)

    graph.update_layout(
        title=graph_name,
        width=600,
        height=600,
        transition={"duration": 3000, "easing": "cubic-in-out"},
        uirevision="heatmap",
    )

    setattr(state, graph_name, graph)


# TODO: Rozdzielić update od kreacji heatmapy, powinna być tworzona raz, chyba że jest zmieniany plik, czyli kiedy selector ma aktywowane on_action. Zwykły update_graph powinien edytować tylko dany obiekt, nie tworzyć nowego graphu


def process_selected_file(state: State, id: str, payload: dict):
    data = load_file(state)

    updated_config = Config(
        MIN_DIST=state.min_dist,
        XMAX=state.xmax,
        YMAX=state.ymax,
        VARIANT=state.variant,
        SHOW_PLOTS=state.show_plots,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    print(f"updated config: {updated_config}")

    processed_data = processor.process_data(
        data.channel_names, data.x_vals_original, data.y_vals_original, updated_config
    )

    update_graph(state, "graph_left", data)
    update_graph(state, "graph_right", processed_data)


### PAGE ###


with tgb.Page() as page:
    tgb.selector(
        value="{config.SHOW_PLOTS}", lov="{show_plots_lov}", on_change=set_show_plots  # type: ignore
    )

    # TODO: Add a CSS class to make the columns fit closer together rather than spreading across the entire width
    with tgb.part():
        with tgb.layout(columns="1 1 1 1"):
            with tgb.part():
                tgb.number(
                    value="{min_dist}",
                    label="Cutoff Distance",
                    on_change=process_selected_file,
                )
            with tgb.part():
                tgb.selector(value="{variant}", lov=variants, on_change=process_selected_file, width="240px", dropdown=True)  # type: ignore
            with tgb.part():
                tgb.number(
                    value="{xmax}", label="Max X", on_change=process_selected_file
                )
            with tgb.part():
                tgb.number(
                    value="{ymax}", label="Max Y", on_change=process_selected_file
                )

    tgb.file_selector(
        content="{file_path}", on_action=process_selected_file, extensions=".fcs"
    )
    tgb.text("Selected file path: {file_path}")

    # tgb.button("Process data", on_action=process_data)

    with tgb.layout(columns="1 1"):
        with tgb.part():
            tgb.chart(figure="{graph_left}")
        with tgb.part():
            tgb.chart(figure="{graph_right}")

if __name__ == "__main__":
    Gui(page=page).run(
        title="duppa", dark_mode=True, debug=True, watermark="", use_reloader=True
    )
