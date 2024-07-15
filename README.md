# TG LAB software

## Setup

How to setup the python environment and install the package to run its functionality

### 1. Build the python environment

Have conda installed and run the following commands in a terminal while in the top level project directory `tg_lab`

```
conda env create -f environment.yml
conda activate tg_lab
pip install -e .
```

### 2. Calculate ion signals values from a data csv

The `ion-signals` entry point runs the functionality to take a dataset from a csv and produce another csv with the identified ions' row, column, radius, and integrated signal.

For more information, run
```
ion-signals --help
```

You should see the following result:

```
Usage: ion-signals [OPTIONS]

Options:
  -i, --input-file TEXT     input csv data file  [required]
  -d, --output-dir TEXT     output directory  [required]
  -t, --output-target TEXT  output file name  [default: ion-signals]
  --help                    Show this message and exit.
```