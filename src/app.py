from dash import Dash, dcc, html, Input, Output, State, callback, ctx
from flask_caching import Cache
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

### ===========

file_path = ""
graph_left = None
graph_right = None


def load_file_from_path(file: str) -> GraphData:
    return processor.load_file_from_base64(file)


# TODO: Rozdzielić update od kreacji heatmapy, powinna być tworzona raz, chyba że jest zmieniany plik, czyli kiedy selector ma aktywowane on_action. Zwykły update_graph powinien edytować tylko dany obiekt, nie tworzyć nowego graphu


def build_figure(graph: GraphData):
    fig = create_heatmap(graph, config, "")
    return fig


@callback(Input("file-upload", "contents"), prevent_initial_call=True)
def file_upload_handler(contents):
    graph_data = load_file_from_path(contents)
    cache.set("graph_data", graph_data)


@callback(
    Output("graph-left", "figure"),
    Output("graph-right", "figure"),
    Input("min-dist", "value"),
    Input("xmax", "value"),
    Input("ymax", "value"),
    Input("variant", "value"),
    prevent_initial_call=True,
)
def process_file(min_dist, xmax, ymax, variant):
    graph_data = cache.get("graph_data")

    cfg = Config(
        MIN_DIST=min_dist,
        XMAX=xmax,
        YMAX=ymax,
        VARIANT=variant,
        SHOW_PLOTS=False,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    processed = processor.process_data(
        graph_data.channel_names,
        graph_data.x_vals_original,
        graph_data.y_vals_original,
        cfg,
    )

    fig_left = build_figure(graph_data)
    fig_right = build_figure(processed)

    return fig_left, fig_right


### PAGE ###


app = Dash(__name__)

cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

app.layout = html.Div(
    [
        dcc.Store(id="graph-left-store"),
        dcc.Store(id="graph-right-store"),
        # Controls
        html.Div(
            [
                dcc.Input(id="min-dist", type="number", value=0),
                dcc.Dropdown(
                    id="variant",
                    options=[{"label": v, "value": v} for v in variants],
                    value="Above",
                ),
                dcc.Input(id="xmax", type="number", value=250000),
                dcc.Input(id="ymax", type="number", value=250000),
            ],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr"},
        ),
        dcc.Upload(
            id="file-upload", children=html.Button("Upload .fcs file"), multiple=False
        ),
        html.Div(id="file-path-display"),
        # Graphs
        html.Div(
            [
                dcc.Graph(id="graph-left"),
                dcc.Graph(id="graph-right"),
            ],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr"},
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True, dev_tools_hot_reload=True)
