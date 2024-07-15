from pathlib import Path

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
def entry_point(
    input_file: str,
    output_dir: str,
    output_target: str = "ion-signals",
) -> None:
    with open(input_file, "r") as f:
        data = np.loadtxt(f, delimiter=",")

    res: pl.DataFrame = ipc.get_ion_signals(data)

    out_dir = Path(output_dir).resolve()
    res.write_csv(out_dir / output_target + ".csv")


if __name__ == "__main__":
    entry_point()
