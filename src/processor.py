from config import Config
import numpy as np
import pandas as pd
from flowio import FlowData
from io import BytesIO
import base64
import tempfile
import os

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.pipeline import make_pipeline
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from graph_drawer import GraphData


class ProcessedData:
    def __init__(self, channel_names, data):
        self.channel_names = channel_names
        self.data = data


def load_fcs(file: str | BytesIO) -> tuple[list, pd.DataFrame]:
    """
    Loads FCS data from a file and returns both the FlowData object and a DataFrame containing the events.
    """
    fcs = FlowData(file)
    if not fcs:
        raise ValueError("file does not exist")

    channel_names = [fcs.channels[i]["pnn"] for i in fcs.channels]
    n_channels = len(channel_names)
    events = np.asarray(fcs.events).reshape(-1, n_channels)

    df = pd.DataFrame(events, columns=channel_names)

    return channel_names, df


def load_file_from_base64(contents: str) -> GraphData:
    """contents has this structure:
    [
        "data:application/octet-stream;base64",
        "SGVsbG8..."
    ]"""
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".fcs") as tmp:
        tmp.write(decoded)
        tmp_path = tmp.name

    try:
        channel_names, unprocessed_data = load_fcs(tmp_path)

        x_vals, y_vals = extract_data(unprocessed_data)
        x_smooth, y_smooth = fit_curve(x_vals, y_vals)

        return GraphData(
            channel_names,
            x_vals,
            y_vals,
            x_vals,
            y_vals,
            x_smooth,
            y_smooth,
            None,
        )
    finally:
        os.remove(tmp_path)


def extract_data(df: pd.DataFrame):
    """
    Preprocesses the data by extracting the columns corresponding to FSC-A and FSC-H
    and returning them as a DataFrame along with separate Series for x and y values.
    This works with the standard structure of FCS files.
    """
    # Get FSC-A, FSC-H
    try:
        fscatters = df[["FSC-A", "FSC-H"]]
    except Exception as e:
        raise ValueError("DataFrame does not have columns for FSC-A and FSC-H") from e

    x_vals = fscatters.iloc[:, 0]
    y_vals = fscatters.iloc[:, 1]

    if x_vals.empty or y_vals.empty:
        raise ValueError("data is empty")

    return x_vals, y_vals


def fit_curve(x_vals, y_vals):
    """
    Fits a smooth curve to the provided x and y values using a pipeline that
    includes a SplineTransformer and LinearRegression.
    """
    model = make_pipeline(SplineTransformer(n_knots=5, degree=3), LinearRegression())
    x_vals = x_vals.to_numpy().reshape(-1, 1)
    model.fit(x_vals, y_vals)

    x_smooth = np.linspace(x_vals.min(), x_vals.max(), 1000).reshape(-1, 1)
    x_smooth = x_smooth
    y_smooth = model.predict(x_smooth)

    return x_smooth.flatten(), y_smooth


def compute_mask(x_vals, y_vals, x_smooth, y_smooth, config: Config):
    """
    Computes a boolean mask for the data points based on their distance from the fitted curve.
    """
    x_vals = np.asarray(x_vals)
    y_vals = np.asarray(y_vals)

    points = np.column_stack((x_vals, y_vals))

    curve = np.column_stack((x_smooth, y_smooth))

    distances = cdist(points, curve)
    min_dist = distances.min(axis=1)

    curve_interp = interp1d(
        curve[:, 0], curve[:, 1], kind="linear", fill_value="extrapolate"
    )

    y_curve = curve_interp(x_vals)

    close = min_dist <= config.MIN_DIST
    far = ~close
    above = y_vals > y_curve
    below = y_vals < y_curve

    match config.VARIANT:
        case "Below":  # cut beneath the curve
            mask = ~(above & far)
        case "Above":  # cut above the curve
            mask = ~(below & far)
        case "Both":  # cut both above and beneath the curve
            mask = ~far
        case _:  # default to cutting beneath the curve
            mask = ~(above & far)

    return points, mask


def filter_data(points, mask):
    return points[mask]


def process_data(channel_names, x, y, config: Config):
    """
    Main processing function that orchestrates the preprocessing, curve fitting,
    mask computation, data filtering, and heatmap creation for a given FCS file.
    """
    x_smooth, y_smooth = fit_curve(x, y)
    points, mask = compute_mask(x, y, x_smooth, y_smooth, config)
    filtered = filter_data(points, mask)

    x_filtered = filtered[:, 0]
    y_filtered = filtered[:, 1]

    return GraphData(
        channel_names, x, y, x_filtered, y_filtered, x_smooth, y_smooth, mask
    )
