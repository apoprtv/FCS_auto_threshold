#!/usr/bin/env python
# coding: utf-8

import os
from config import Config

print("Starting FCS data processor...", flush=True)

from processor import Processor

if __name__ == "__main__":
    print("Welcome to FCS data processor!", flush=True)

    config = Config(
        MIN_DIST=0,
        XMAX=250000,
        YMAX=250000,
        BINS=1000,
        SHOW_PLOTS=False,
        SAVE_PLOTS=False,
        VARIANT=0,
    )

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
    config.SHOW_PLOTS = bool(input() or 0)

    print("Save plots? (1 for yes, 0 for no): ", end="", flush=True)
    config.SAVE_PLOTS = bool(input() or 0)

    while True:
        files = []
        processor = Processor()

        if directory[len(directory) - 3 :] == "fcs":
            result = processor.process(directory, config=config)

        elif directory == "" or not directory:
            files = os.listdir(os.getcwd())

        else:
            files = os.listdir(directory)

        if files:
            for path in files:
                if path.endswith(".fcs"):
                    result = processor.process(path, config=config)
                    print("Processing completed!", flush=True)
                    if config.SHOW_PLOTS:
                        print("Accept the filtered data? (1 for yes, 0 for no): ")
                        user_accept = bool(int(input() or 0))
                        if user_accept and config.SAVE_PLOTS:
                            processor.save(result, config=config)
                        else:
                            print(
                                "Data not saved. Moving to the next file.", flush=True
                            )

        if not files or not any(file.endswith(".fcs") for file in files):
            print("No files found in the specified directory.", flush=True)
