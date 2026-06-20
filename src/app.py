from taipy.gui import Gui
from taipy.gui.state import State
import taipy.gui.builder as tgb
import numpy as np
import plotly.graph_objects as go
from config import Config
import processor
from graph_drawer import create_heatmap, GraphData

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
show_points = False
original_graph_data = None
graph_left = None
graph_right = None


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

    graph = create_heatmap(
        graph_data, updated_config, state.show_points, state.file_path
    )

    graph.update_layout(
        title=graph_name,
        autosize=True,
        transition={"duration": 300, "easing": "cubic-in-out"},
        showlegend=False,
    )

    setattr(state, graph_name, graph)


# TODO: Rozdzielić update od kreacji heatmapy, powinna być tworzona raz, chyba że jest zmieniany plik, czyli kiedy selector ma aktywowane on_action. Zwykły update_graph powinien edytować tylko dany obiekt, nie tworzyć nowego graphu


def load_file(state: State) -> None:
    channel_names, unprocessed_data = processor.load_fcs(state.file_path)
    x_vals, y_vals = processor.extract_data(unprocessed_data)
    x_smooth, y_smooth = processor.fit_curve(x_vals, y_vals)
    original_graph_data = GraphData(
        channel_names, x_vals, y_vals, x_vals, y_vals, x_smooth, y_smooth, None
    )
    state.original_graph_data = original_graph_data


def load_selected_file(state: State) -> None:
    load_file(state)
    process_selected_file(state=state)


def process_selected_file(state: State, trigger=None) -> None:
    data = getattr(state, "original_graph_data", None)

    if data is None:
        print("No data is loaded")
        return

    updated_config = Config(
        MIN_DIST=state.min_dist,
        XMAX=state.xmax,
        YMAX=state.ymax,
        VARIANT=state.variant,
        SHOW_PLOTS=state.show_plots,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    processed_data = processor.process_data(
        data.channel_names, data.x_vals_original, data.y_vals_original, updated_config
    )

    update_graph(state, "graph_left", data)
    update_graph(state, "graph_right", processed_data)


### PAGE ###


with tgb.Page() as page:
    # tgb.selector(
    #     value="{config.SHOW_PLOTS}", lov="{show_plots_lov}", on_change=set_show_plots  # type: ignore
    # )

    # TODO: Add a CSS class to make the columns fit closer together rather than spreading across the entire width
    with tgb.part(class_name="sticky-bar"):
        with tgb.layout(columns="1 1 1 1"):
            with tgb.part():
                tgb.number(
                    value="{min_dist}",
                    label="Cutoff Distance",
                    on_change=process_selected_file,
                    change_delay=500,
                )
            with tgb.part():
                tgb.selector(value="{variant}", lov=variants, on_change=process_selected_file, width="240px", dropdown=True)  # type: ignore
            with tgb.part():
                tgb.number(
                    value="{xmax}",
                    label="Max X",
                    on_change=process_selected_file,
                    change_delay=500,
                )
            with tgb.part():
                tgb.number(
                    value="{ymax}",
                    label="Max Y",
                    on_change=process_selected_file,
                    change_delay=500,
                )

    tgb.file_selector(
        content="{file_path}", on_action=load_selected_file, extensions=".fcs"
    )

    # tgb.button("Process data", on_action=process_data)

    tgb.toggle(
        value="{show_points}",
        allow_unselect=True,
        label="Show Points",
        on_change=lambda state: process_selected_file(state, "show_points"),
    )

    with tgb.layout(columns="1 1"):
        with tgb.part():
            tgb.chart(figure="{graph_left}", class_name="square-chart")
        with tgb.part():
            tgb.chart(figure="{graph_right}", class_name="square-chart")

if __name__ == "__main__":
    Gui(page=page, css_file="styles.css").run(
        title="duppa", dark_mode=True, debug=True, watermark="", use_reloader=True
    )
