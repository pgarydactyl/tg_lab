from pathlib import Path
from tg_lab.utils import get_event_id
import json
import os

import numpy as np

from .constants import RawIndices


def get_files(path: str | Path, glob=r"**\*.txt"):
    path = Path(path)
    yield from path.glob(glob)


def prepare_experiment_dir(path: str | Path, name="tof"):
    path = Path(path)
    output_dir = path / get_event_id(name)
    os.makedirs(output_dir)
    return output_dir


def parse_file_path(path: str | Path, delimiter: str = "_"):
    """
    Files are expected to have the following naming structure:
    `{title}_{time}_{run}.txt`

    Where `_` is the default delimiter
    """
    path = Path(path)
    pieces = path.stem.split(delimiter)
    time, run = pieces[-2:]
    title = delimiter.join(pieces[:-2])

    return title, time, run


def parse_data(path: str | Path):
    """
    Read the data within an experimental data file

    The data is expected to be a single column with time and signal
    data stacked on top of one another
    """
    path = Path(path)
    data = np.loadtxt(path)
    midpoint = data.shape[0] // 2

    time = data[:midpoint]
    signal = data[midpoint:]

    return {
        RawIndices.TOF_TIME.value: time,
        RawIndices.SIGNAL.value: signal,
    }


def write_json(path, data):
    with open(Path(path), "w") as f:
        json.dump(data, f, indent=4)
