from dataclasses import dataclass


@dataclass
class Config:
    MIN_DIST: int
    XMAX: int
    YMAX: int
    BINS: int
    SHOW_PLOTS: bool
    SAVE_PLOTS: bool
    VARIANT: int
