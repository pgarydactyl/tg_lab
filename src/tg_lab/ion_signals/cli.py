from pathlib import Path
from typing import List

import click
import numpy as np
import polars as pl

import tg_lab.ion_signals.compute as ipc


@click.command()
@click.option(
    "--input-file",
    "-i",
    required=True,
    help="input csv data file",
)
@click.option(
    "--output-dir",
    "-d",
    required=True,
    help="output directory",
)
@click.option(
    "--output-target",
    "-t",
    required=False,
    help="output file name",
    default="ion-signals",
    show_default=True,
)
@click.option(
    "--integration-fns",
    "-f",
    multiple=True,
    required=False,
    help="type of signal integration function to use, options include [box, l1, l2]",
    default=["box"],
    show_default=True,
)
def entry_point(
    input_file: str,
    output_dir: str,
    output_target: str,
    integration_fns: List[str],
) -> None:
    with open(input_file, "r") as f:
        data = np.loadtxt(f, delimiter=",")

    res: pl.DataFrame = ipc.get_ion_signals(
        data,
        integration_fns=integration_fns,
    )

    out_dir = Path(output_dir).resolve()
    path = out_dir / output_target
    res.write_csv(path.with_suffix(".csv"))


if __name__ == "__main__":
    entry_point()
