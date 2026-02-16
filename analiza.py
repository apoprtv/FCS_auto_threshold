#!/usr/bin/env python
# coding: utf-8

print("Starting FCS data processor...", flush=True)

import os
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

MIN_DIST = 0  # Minimum acceptable distance from the curve for a point to be included in the filtered data
XMAX, YMAX = 250000, 250000  # Maximum values for x and y axes in the heatmap
BINS = 1000  # Number of bins for the heatmap


class Processor:
    def create_heatmap(
        self,
        x,
        y,
        filename: str,
        name: str,
    ):
        heatmap, xedges, yedges = np.histogram2d(
            x, y, bins=BINS, range=[[0, XMAX], [0, YMAX]]
        )

        # Normalize heatmap
        heatmap = heatmap / heatmap.max()

        plt.figure()
        hm = sns_heatmap(heatmap.T, cmap="viridis")
        hm.invert_yaxis()
        plt.savefig(f"{filename}_{name}_heatmap.png")

    def _load_fcs(self, filename: str):
        fcs = FlowData(filename)

        if not fcs:
            raise ValueError("file does not exist")

        n_channels = len(fcs.channels)
        events = np.asarray(fcs.events).reshape(-1, n_channels)
        df = pd.DataFrame(events, columns=fcs.channels)
        return fcs, df

    def _preprocess_data(self, df: pd.DataFrame):
        # Get FSC-A, FSC-H
        fscatters = df.iloc[:, :2]

        x = fscatters.iloc[:, 0]
        y = fscatters.iloc[:, 1]

        if fscatters.empty or x.empty or y.empty:
            raise ValueError("data is empty")

        return fscatters, x, y

    def _fit_curve(self, x, y):
        model = make_pipeline(
            SplineTransformer(n_knots=5, degree=3), LinearRegression()
        )
        x_vals = x.to_numpy().reshape(-1, 1)
        model.fit(x_vals, y)

        x_smooth = np.linspace(x.min(), x.max(), 1000).reshape(-1, 1)
        y_smooth = model.predict(x_smooth)

        return x_smooth, y_smooth

    def _compute_mask(self, fscatters, x_smooth, y_smooth):
        points = fscatters.iloc[:, :3].to_numpy()
        curve = np.column_stack((x_smooth, y_smooth))

        distances = cdist(points, curve)

        min_dist = distances.min(axis=1)

        curve_interp = interp1d(
            curve[:, 0], curve[:, 1], kind="linear", fill_value="extrapolate"
        )

        y_curve_interpolated_points = curve_interp(fscatters.iloc[:, 0])

        mask = (fscatters.iloc[:, 1] > y_curve_interpolated_points) | (
            min_dist <= MIN_DIST
        )

        return mask

    def _filter_data(self, df, mask):
        return df[mask]

    def process(self, filename):
        fcs, df = self._load_fcs(filename)

        fscatters, x, y = self._preprocess_data(df)

        # Get original heatmap
        self.create_heatmap(x, y, filename, name="original")

        x_smooth, y_smooth = self._fit_curve(x, y)

        mask = self._compute_mask(fscatters, x_smooth, y_smooth)

        filtered = self._filter_data(df, mask)

        channel_names = fcs.pnn_labels
        write_fcs(
            filename=f"{filename[:len(filename)-4]}_filtered.fcs",
            chn_names=channel_names,
            data=filtered.to_numpy(),
        )

        # Draw new heatmap
        self.create_heatmap(
            filtered.iloc[:, 0], filtered.iloc[:, 1], filename, name="filtered"
        )


if __name__ == "__main__":
    print("Welcome to FCS data processor!", flush=True)

    print("directory or filename: ", end="", flush=True)
    directory = input()

    print("minimal acceptable distance: ", end="", flush=True)
    MIN_DIST = int(input() or 0)

    print("max value for x axis (leave empty for default 250000): ", end="", flush=True)
    XMAX = int(input() or 250000)

    print("max value for y axis (leave empty for default 250000): ", end="", flush=True)
    YMAX = int(input() or 250000)

    files = []

    processor = Processor()

    if directory[len(directory) - 3 :] == "fcs":
        processor.process(directory)

    elif directory == "" or not directory:
        files = os.listdir(os.getcwd())

    else:
        files = os.listdir(directory)

    if files:
        for path in files:
            if path.endswith(".fcs"):
                processor.process(path)

    print("Processing completed!", flush=True)
