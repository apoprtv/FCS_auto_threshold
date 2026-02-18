import config
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


class Processor:
    def _create_heatmap(
        self,
        x_vals,
        y_vals,
        filename: str,
        name: str,
    ):
        """
        Creates and saves a heatmap based on the provided x and y values.
        The heatmap is saved as a PNG file with a name based on the original filename and a specified name (e.g., "original" or "filtered").
        """
        heatmap, xedges, yedges = np.histogram2d(
            x_vals, y_vals, bins=config.BINS, range=[[0, config.XMAX], [0, config.YMAX]]
        )
        heatmap = heatmap / heatmap.max()

        # heatmap requires figure and transposition to display correctly
        plt.figure()
        plt.title(f"{name}")
        hm = sns_heatmap(heatmap.T, cmap="viridis")
        hm.invert_yaxis()
        plt.savefig(f"{filename}_{name}_heatmap.png")

        if config.SHOW_PLOTS:
            plt.show()

    def _load_fcs(self, filename: str):
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

    def _compute_mask(self, fscatters, x_smooth, y_smooth):
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

        mask = (fscatters.iloc[:, 1] > y_curve_interpolated_points) | (
            min_dist <= config.MIN_DIST
        )

        return mask

    def _filter_data(self, df, mask):
        return df[mask]

    def _process(self, filename):
        """
        Main processing function that orchestrates the loading, preprocessing, curve fitting,
        mask computation, data filtering, and heatmap creation for a given FCS file.
        """
        fcs, df = self._load_fcs(filename)

        fscatters, x, y = self._preprocess_data(df)

        self._create_heatmap(x, y, filename, name="original")

        x_smooth, y_smooth = self._fit_curve(x, y)

        mask = self._compute_mask(fscatters, x_smooth, y_smooth)

        filtered = self._filter_data(df, mask)

        channel_names = fcs.pnn_labels

        write_fcs(
            filename=f"{filename[:len(filename)-4]}_filtered.fcs",
            chn_names=channel_names,
            data=filtered.to_numpy(),
        )

        self._create_heatmap(
            filtered.iloc[:, 0], filtered.iloc[:, 1], filename, name="filtered"
        )
