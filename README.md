# TG LAB software

## Setup

How to setup the python environment and install the package to run its functionality

### 1. Build the python environment

Have conda installed and run the following commands in a terminal while in the top level project directory `tg_lab`

```
conda env create --file=environment.yml
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

## Control 33U Series Camera with `tis_camera` module

Ensure the following packages have been installed from the company [website](https://www.theimagingsource.com/en-us/product/industrial/33u/dmk33ux174/)
- [GenTL Producer for USB3 Vision Cameras](https://www.theimagingsource.com/en-us/support/download/ic4gentlprodu3vwintis-1.3.1.501/)
- [Device Driver for USB 33U, 37U, 38U, 32U Cameras and DFG/HDMI Converter](https://www.theimagingsource.com/en-us/support/download/icwdmuvccamtis33u-5.2.0.2768/)
- [IC Imaging Control 4 SDK](https://www.theimagingsource.com/en-us/support/download/icimagingcontrol4win-1.2.0.2954/)

Run the `tis_camera` module through the command line to capture and process images
