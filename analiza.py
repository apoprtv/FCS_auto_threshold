#!/usr/bin/env python
# coding: utf-8

import os
import config

print("Starting FCS data processor...", flush=True)

from file_processor import Processor


if __name__ == "__main__":
    print("Welcome to FCS data processor!", flush=True)

    print("directory or filename: ", end="", flush=True)
    directory = input()

    print("minimal acceptable distance: ", end="", flush=True)
    config.MIN_DIST = int(input() or 0)

    print("max value for x axis (leave empty for default 250000): ", end="", flush=True)
    config.XMAX = int(input() or 250000)

    print("max value for y axis (leave empty for default 250000): ", end="", flush=True)
    config.YMAX = int(input() or 250000)

    print("Show plots? (1 for yes, 0 for no): ", end="", flush=True)
    config.SHOW_PLOTS = int(input() or 0)

    files = []

    processor = Processor()

    if directory[len(directory) - 3 :] == "fcs":
        processor._process(directory)

    elif directory == "" or not directory:
        files = os.listdir(os.getcwd())

    else:
        files = os.listdir(directory)

    if files:
        for path in files:
            if path.endswith(".fcs"):
                processor._process(path)

    print("Processing completed!", flush=True)
