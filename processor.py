from config import Config
import numpy as np
import pandas as pd
from flowio import FlowData
from seaborn import heatmap as sns_heatmap
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.pipeline import make_pipeline
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from fcswrite import write_fcs


class ProcessedData:
    def __init__(self, channel_names, data):
        self.channel_names = channel_names
        self.data = data


def _create_heatmap(self, x_vals, y_vals, config: Config, filename: str, name: str):
    """
    Creates and saves a heatmap based on the provided x and y values.
    The heatmap is saved as a PNG file with a name based on the original filename and a specified name (e.g., "original" or "filtered").
    """
    heatmap, xedges, yedges = np.histogram2d(
        x_vals, y_vals, bins=config.BINS, range=[[0, config.XMAX], [0, config.YMAX]]
    )
    heatmap = heatmap / heatmap.max()

    if config.SHOW_PLOTS or config.SAVE_PLOTS:
        self._create_heatmap_plot(
            x_vals,
            y_vals,
            filename,
            name,
            heatmap,
            config.SHOW_PLOTS,
            config.SAVE_PLOTS,
        )

    return heatmap

def _create_heatmap_plot(
    self,
    x_vals,
    y_vals,
    filename: str,
    name: str,
    heatmap: np.ndarray,
    show_plots: bool,
    save_plots: bool,
):
    plt.figure()
    plt.title(f"{name}")
    hm = sns_heatmap(heatmap.T, cmap="viridis")
    hm.invert_yaxis()

    if show_plots:
        plt.show()

    if save_plots:
        plt.savefig(f"{filename}_{name}_heatmap.png")

def _preprocess_data(self, df: pd.DataFrame):
    """
    Preprocesses the data by extracting the first two columns (assumed to be FSC-A and FSC-H)
    and returning them as a DataFrame along with separate Series for x and y values.
    This works with the standard structure of FCS files.
    """
    # Get FSC-A, FSC-H
    fscatters = df.iloc[:, :2]

    x_vals = fscatters.iloc[:, 0]
    y_vals = fscatters.iloc[:, 1]

    if fscatters.empty or x_vals.empty or y_vals.empty:
        raise ValueError("data is empty")

    return fscatters, x_vals, y_vals

def _fit_curve(self, x_vals, y_vals):
    """
    Fits a smooth curve to the provided x and y values using a pipeline that
    includes a SplineTransformer and LinearRegression.
    """
    model = make_pipeline(
        SplineTransformer(n_knots=5, degree=3), LinearRegression()
    )
    x_vals = x_vals.to_numpy().reshape(-1, 1)
    model.fit(x_vals, y_vals)

    x_smooth = np.linspace(x_vals.min(), x_vals.max(), 1000).reshape(-1, 1)
    y_smooth = model.predict(x_smooth)

    return x_smooth, y_smooth

def _compute_mask(self, fscatters, x_smooth, y_smooth, config: Config):
    """
    Computes a boolean mask for the data points based on their distance from the fitted curve.
    """
    points = fscatters.iloc[:, :3].to_numpy()
    curve = np.column_stack((x_smooth, y_smooth))

    distances = cdist(points, curve)

    min_dist = distances.min(axis=1)

    curve_interp = interp1d(
        curve[:, 0], curve[:, 1], kind="linear", fill_value="extrapolate"
    )

    y_curve_interpolated_points = curve_interp(fscatters.iloc[:, 0])

    match config.VARIANT:
        case 0:  # cut beneath the curve
            mask = (fscatters.iloc[:, 1] > y_curve_interpolated_points) | (
                min_dist <= config.MIN_DIST
            )
        case 1:  # cut above the curve
            mask = (fscatters.iloc[:, 1] < y_curve_interpolated_points) | (
                min_dist <= config.MIN_DIST
            )
        case 2:  # cut both above and beneath the curve
            mask = (
                (fscatters.iloc[:, 1] > y_curve_interpolated_points)
                | (min_dist <= config.MIN_DIST)
            ) & (
                (fscatters.iloc[:, 1] < y_curve_interpolated_points)
                | (min_dist <= config.MIN_DIST)
            )
        case _:  # default to cutting beneath the curve
            mask = (fscatters.iloc[:, 1] > y_curve_interpolated_points) | (
                min_dist <= config.MIN_DIST
            )

    return mask

def _filter_data(self, df, mask):
    return df[mask]

def load_fcs(self, filename: str):
    """
    Loads FCS data from a file and returns both the FlowData object and a DataFrame containing the events.
    """
    fcs = FlowData(filename)
    if not fcs:
        raise ValueError("file does not exist")

    n_channels = len(fcs.channels)
    events = np.asarray(fcs.events).reshape(-1, n_channels)

    df = pd.DataFrame(events, columns=fcs.channels)

    return fcs, df

def process(self, fcs, df, config: Config):
    """
    Main processing function that orchestrates the loading, preprocessing, curve fitting,
    mask computation, data filtering, and heatmap creation for a given FCS file.
    """
    df_original = df.copy()

    fscatters, x, y = self._preprocess_data(df_original)
    x_smooth, y_smooth = self._fit_curve(x, y)
    mask = self._compute_mask(fscatters, x_smooth, y_smooth, config)
    filtered = self._filter_data(fscatters, mask)
    filtered_dict = {
        "x": filtered.iloc[:, 0].to_numpy(),
        "y": filtered.iloc[:, 1].to_numpy(),
    }
    channel_names = fcs.pnn_labels

    return ProcessedData(channel_names, filtered_dict)

def make_heatmap(self, x, y, config: Config, filename: str):
    heatmap = self._create_heatmap(x, y, config, filename, name="original")
    return heatmap

def save(self, processed_data: ProcessedData, config: Config, filename: str):
    channel_names = processed_data.channel_names
    data = processed_data.data

    df = pd.DataFrame(data)

    write_fcs(
        filename=f"{filename[:len(filename)-4]}_filtered.fcs",
        chn_names=channel_names,
        data=df.to_numpy(),
    )

    self._create_heatmap(
        data.iloc[:, 0], data.iloc[:, 1], config, filename, name="filtered"
    )
