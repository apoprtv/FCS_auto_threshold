#!/usr/bin/env python
# coding: utf-8

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

MIN_DISTANCE = 0
XMAX, YMAX = 250000, 250000
BINS = 1000


class Processor:
    def create_heatmap(
        self,
        x: np.ndarray | pd.Series[int],
        y: np.ndarray | pd.Series[int],
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

    def load_fcs(self, filename: str):
        fcs = FlowData(filename)

        if not fcs:
            raise ValueError("file does not exist")

        n_channels = len(fcs.channels)
        events = np.asarray(fcs.events).reshape(-1, n_channels)
        df = pd.DataFrame(events, columns=fcs.channels)
        return fcs, df

    def preprocess_data(self, df: pd.DataFrame):
        # Get FSC-A, FSC-H
        fscatters = df.iloc[:, :2]

        x = fscatters.iloc[:, 0]
        y = fscatters.iloc[:, 1]

        if fscatters.empty or x.empty or y.empty:
            raise ValueError("data is empty")

        return fscatters, x, y

    def fit_curve(self, x, y):
        model = make_pipeline(
            SplineTransformer(n_knots=5, degree=3), LinearRegression()
        )
        x_vals = x.to_numpy().reshape(-1, 1)
        model.fit(x_vals, y)

        x_smooth = np.linspace(x.min(), x.max(), 1000).reshape(-1, 1)
        y_smooth = model.predict(x_smooth)

        return x_smooth, y_smooth

    def compute_mask(self, fscatters, x_smooth, y_smooth):
        points = fscatters.iloc[:, :3].to_numpy()
        curve = np.column_stack((x_smooth, y_smooth))

        distances = cdist(points, curve)

        min_dist = distances.min(axis=1)

        curve_interp = interp1d(
            curve[:, 0], curve[:, 1], kind="linear", fill_value="extrapolate"
        )

        y_curve_interpolated_points = curve_interp(fscatters.iloc[:, 0])

        mask = (fscatters.iloc[:, 1] > y_curve_interpolated_points) | (
            min_dist <= MIN_DISTANCE
        )

        return mask

    def filter_data(self, df, mask):
        return df[mask]

    def process(self, filename):
        fcs, df = self.load_fcs(filename)

        fscatters, x, y = self.preprocess_data(df)

        # Get original heatmap
        self.create_heatmap(x, y, filename, name="original")

        x_smooth, y_smooth = self.fit_curve(x, y)

        mask = self.compute_mask(fscatters, x_smooth, y_smooth)

        filtered = self.filter_data(df, mask)

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
    directory = input("directory or filename: ")
    MIN_DISTANCE = int(input("minimal acceptable distance: "))

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
