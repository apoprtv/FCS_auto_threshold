from taipy.gui import Gui
from taipy.gui.gui_actions import notify
from taipy.gui.state import State
import taipy.gui.builder as tgb
from config import Config
import processor
from graph_drawer import create_heatmap, GraphData
from pathlib import Path

config = Config(
    MIN_DIST=100,
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

min_dist = 100
xmax = 250000
ymax = 250000
variant = "Above"
show_plots = False

### ===========

file_paths: list[str] = []
files_dict: dict = {}
files_ui: list[str] = []
selected_file_path: str = ""
selected_file_path_ui: str = ""
show_points = False
channel_names = None
save_path: str = ""
original_df = None
filtered_df = None
original_graph_data = None
graph_left = None
graph_right = None
show_sidebar = False
sidebar_class_name = "tree-overlay-hidden"


def update_graph(state: State, graph_name: str, title: str, graph_data: GraphData):
    if not hasattr(state, graph_name):
        raise ValueError(f"Unidentified graph_name: {graph_name}")

    updated_config = Config(
        MIN_DIST=state.min_dist,
        VARIANT=state.variant,
        SHOW_PLOTS=state.show_plots,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    graph = create_heatmap(
        graph_data, updated_config, state.show_points, state.selected_file_path
    )

    graph.update_layout(
        title=title,
        xaxis=dict(range=[0, max(graph_data.x_vals_original)]),
        yaxis=dict(range=[0, max(graph_data.y_vals_original)]),
        autosize=True,
        transition={"duration": 300, "easing": "cubic-in-out"},
        showlegend=False,
    )

    setattr(state, graph_name, graph)


def load_file(state: State) -> None:
    channel_names, unprocessed_data = processor.load_fcs(state.selected_file_path)
    state.original_df = unprocessed_data
    x_vals, y_vals = processor.extract_data(unprocessed_data)
    x_smooth, y_smooth = processor.fit_curve(x_vals, y_vals)
    original_graph_data = GraphData(
        channel_names, x_vals, y_vals, x_vals, y_vals, x_smooth, y_smooth, None
    )
    state.original_graph_data = original_graph_data


def load_selected_file(state: State) -> None:
    if type(state.file_paths) is not list:
        state.file_paths = [state.file_paths]
    state.selected_file_path = state.file_paths[0]
    load_file(state)
    build_folder_tree(state)
    process_selected_file(state=state)


def build_folder_tree(state: State) -> None:
    files_dict = {}

    for file_path in state.file_paths:
        p = Path(file_path)

        if p.is_file() and p.suffix == ".fcs":
            short_path = "/".join(p.parts[-1:])

            """ The filenames contain temp file indexing, e.g. W96_E9_E09_057.196.fcs,
            the displayed name should not contain them """
            slices = str(short_path).split(".")
            short_path = slices[0] + "." + slices[2]

            files_dict[short_path] = str(p)

    state.files_dict = files_dict
    state.files_ui = list(files_dict.keys())

    return None


def process_selected_file(state: State, trigger=None) -> None:
    graph_data = getattr(state, "original_graph_data", None)
    df = getattr(state, "original_df", None)

    if graph_data is None or df is None:
        print("No data is loaded")
        return

    updated_config = Config(
        MIN_DIST=state.min_dist,
        VARIANT=state.variant,
        SHOW_PLOTS=state.show_plots,
        SAVE_PLOTS=False,
        BINS=1000,
    )

    processed_data, df_filtered, channel_names = processor.process_data(
        graph_data.channel_names, df, updated_config
    )

    state.filtered_df = df_filtered
    state.channel_names = channel_names

    update_graph(state, "graph_left", "Original", graph_data)
    update_graph(state, "graph_right", "Filtered", processed_data)


def process_selected_file_ui(state: State):
    new_selected_file_path = state.files_dict.get(state.selected_file_path_ui[0], "")

    if new_selected_file_path != "":
        state.selected_file_path = new_selected_file_path

    load_file(state)
    process_selected_file(state)


def save_filtered_data(state: State):
    try:
        save_path = processor.save_fcs(
            state.channel_names,
            state.selected_file_path,
            state.save_path,
            state.filtered_df,
        )
        notify(state, "success", f"Saved to: {save_path}")
    except Exception as e:
        notify(state, "error", f"Error while saving: {e}")


def batch_save_filtered_data(state: State):
    for file_path in state.file_paths:
        channel_names, df = processor.load_fcs(file_path)
        _, df_filtered, channel_names = processor.process_data(
            channel_names, df, state.config
        )
        try:
            save_path = processor.save_fcs(
                channel_names, file_path, state.save_path, df_filtered
            )
            notify(state, "success", f"Saved to: {save_path}")
        except Exception as e:
            notify(state, "error", f"Error while saving: {e}")


def toggle_sidebar(state: State):
    state.show_sidebar = not state.show_sidebar

    if state.show_sidebar:
        state.sidebar_class_name = "tree-overlay-visible"
    else:
        state.sidebar_class_name = "tree-overlay-hidden"


### PAGE ###


with tgb.Page() as page:
    with tgb.layout(columns="0.25 1 1"):
        with tgb.part(class_name=""):
            with tgb.layout(columns="1"):
                with tgb.part():
                    tgb.file_selector(
                        content="{file_paths}",
                        multiple=True,
                        on_action=load_selected_file,
                        extensions=".fcs",
                    )
                with tgb.part():
                    tgb.toggle(
                        value="{show_points}",
                        allow_unselect=True,
                        label="Show Points",
                        on_change=lambda state: process_selected_file(
                            state, "show_points"
                        ),
                    )
                with tgb.part():
                    tgb.number(
                        value="{min_dist}",
                        label="Cutoff Distance",
                        on_change=process_selected_file,
                        change_delay=500,
                    )
                with tgb.part():
                    tgb.selector(value="{variant}", label="Cutoff Variant", lov=variants, on_change=process_selected_file, dropdown=True)  # type: ignore
                with tgb.part():
                    tgb.input("{save_path}", label="Save path")
                with tgb.part():
                    tgb.button("Save", on_action=save_filtered_data)
                with tgb.part():
                    tgb.button("Batch Save", on_action=batch_save_filtered_data)
        with tgb.part():
            tgb.chart(figure="{graph_left}", class_name="square-chart")
        with tgb.part():
            tgb.chart(figure="{graph_right}", class_name="square-chart")
    with tgb.part(class_name="{sidebar_class_name}"):  # type: ignore
        tgb.tree(
            value="{selected_file_path_ui}",
            lov="{files_ui}",  # type: ignore
            on_change=process_selected_file_ui,
        )
    tgb.button(
        "file selector tree", on_action=toggle_sidebar, class_name="sidebar-button"
    )

if __name__ == "__main__":
    Gui(page=page, css_file="styles.css").run(
        title="duppa", dark_mode=True, debug=True, watermark="", use_reloader=True
    )
