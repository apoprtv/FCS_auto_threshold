import pandas as pd
from fcswrite import write_fcs
from processor import ProcessedData
from config import Config


def save(processed_data: ProcessedData, config: Config, filename: str):
    channel_names = processed_data.channel_names
    data = processed_data.data

    df = pd.DataFrame(data)

    write_fcs(
        filename=f"{filename[:len(filename)-4]}_filtered.fcs",
        chn_names=channel_names,
        data=df.to_numpy(),
    )


def change_category(state):
    pass
