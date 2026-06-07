from config import Config
import numpy as np
import pandas as pd
from flowio import FlowData

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import SplineTransformer
from sklearn.pipeline import make_pipeline
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d


class ProcessedData:
    def __init__(self, channel_names, data):
        self.channel_names = channel_names
        self.data = data


def load_fcs(filename: str):
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


def excract_data(df: pd.DataFrame):
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

    if fscatters.empty or x_vals.empty or y_vals.empty:
        raise ValueError("data is empty")

    return fscatters, x_vals, y_vals


def fit_curve(x_vals, y_vals):
    """
    Fits a smooth curve to the provided x and y values using a pipeline that
    includes a SplineTransformer and LinearRegression.
    """
    model = make_pipeline(SplineTransformer(n_knots=5, degree=3), LinearRegression())
    x_vals = x_vals.to_numpy().reshape(-1, 1)
    model.fit(x_vals, y_vals)

    x_smooth = np.linspace(x_vals.min(), x_vals.max(), 1000).reshape(-1, 1)
    y_smooth = model.predict(x_smooth)

    return x_smooth, y_smooth


def compute_mask(fscatters, x_smooth, y_smooth, config: Config):
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


def filter_data(df, mask):
    return df[mask]


def process_data(fcs, df, config: Config):
    """
    Main processing function that orchestrates the loading, preprocessing, curve fitting,
    mask computation, data filtering, and heatmap creation for a given FCS file.
    """
    df_original = df.copy()

    fscatters, x, y = excract_data(df_original)
    x_smooth, y_smooth = fit_curve(x, y)
    mask = compute_mask(fscatters, x_smooth, y_smooth, config)
    filtered = filter_data(fscatters, mask)
    filtered_dict = {
        "x": filtered.iloc[:, 0].to_numpy(),
        "y": filtered.iloc[:, 1].to_numpy(),
    }
    channel_names = fcs.pnn_labels

    return ProcessedData(channel_names, filtered_dict)
