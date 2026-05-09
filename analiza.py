#!/usr/bin/env python
# coding: utf-8

import os
import config

print("Starting FCS data processor...", flush=True)

from file_processor import Processor


if __name__ == "__main__":
    print("Welcome to FCS data processor!", flush=True)

    while True:

        print("directory or filename: ", end="", flush=True)
        directory = input()

        print("minimal acceptable distance: ", end="", flush=True)
        config.MIN_DIST = int(input() or 0)

        print(
            "Choose variant for cutting data points (0 for beneath the curve, 1 for above the curve, 2 for both): ",
            end="",
            flush=True,
        )
        variant = int(input() or 0)

        print(
            "max value for x axis (leave empty for default 250000): ",
            end="",
            flush=True,
        )
        config.XMAX = int(input() or 250000)

        print(
            "max value for y axis (leave empty for default 250000): ",
            end="",
            flush=True,
        )
        config.YMAX = int(input() or 250000)

        print("Show plots? (1 for yes, 0 for no): ", end="", flush=True)
        show_plots = bool(input() or 0)

        files = []

        processor = Processor()

        if directory[len(directory) - 3 :] == "fcs":
            processor.process(directory, variant=variant, show_plots=show_plots)

        elif directory == "" or not directory:
            files = os.listdir(os.getcwd())

        else:
            files = os.listdir(directory)

        if files:
            for path in files:
                if path.endswith(".fcs"):
                    processor.process(path, variant=variant, show_plots=show_plots)
                    print("Processing completed!", flush=True)

        if not files or not any(file.endswith(".fcs") for file in files):
            print("No files found in the specified directory.", flush=True)
