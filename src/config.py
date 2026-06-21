from dataclasses import dataclass


@dataclass(frozen=False)
class Config:
    MIN_DIST: int
    BINS: int
    SHOW_PLOTS: bool
    SAVE_PLOTS: bool
    VARIANT: str
