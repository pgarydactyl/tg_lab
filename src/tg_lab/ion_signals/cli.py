from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl
import tyro

import tg_lab.ion_signals.compute as ipc


@dataclass
class IntegrationConfig:
    """
    Processes an ion image data file and writes out the results
    """

    input_file: str
    """ion image data file"""

    output_dir: str
    """directory to write output to"""

    output_target: str
    """file name to write output to"""

    integration_fns: list[ipc.IntegrationFns]
    """list of integration functions to sum ion image data"""


def entry_point(config: IntegrationConfig) -> None:
    with open(config.input_file, "r") as f:
        data = np.loadtxt(f, delimiter=",")

    res: pl.DataFrame = ipc.get_ion_signals(
        data,
        integration_fns=config.integration_fns,
    )

    out_dir = Path(config.output_dir).resolve()
    path = out_dir / config.output_target
    res.write_csv(path.with_suffix(".csv"))


if __name__ == "__main__":
    config = tyro.cli(IntegrationConfig)
    entry_point(config)
