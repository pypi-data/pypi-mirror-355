# Lemna
A simple app utilizing computer vision which identifies wells and calculates the area for any region that matches the given mask (HSV lower-upper).

## Getting Started

### Installing
Install via `pip` (recommended to use a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)):

`pip install lemna`


### Usage

This tool provides several commands via the CLI.
You can use the app by typing `lemna` in the terminal. Typing `lemna --help` will show available commands.


#### threshold — Tune HSV Thresholds

Determine optimal HSV thresholds for identifying areas of interest in wells.

`lemna threshold -i path/to/image.jpg -w 640 -c config.toml`

Options:

- `-i, --image`: Path to the image file
- `-w, --width`: Optional display width for thresholding UI
- `-c, --config`: Path to the config file to update HSV values

#### process — Analyze Images

Detect wells, analyze plant area, and output CSV + annotated images.

`lemna process -i path/to/image_or_folder -o ./output -c config.toml`

Options:
- `-i, --image`: Path to image or folder of images
- `-o, --output`: Output directory
- `-c, --config`: Path to config file
- `--dp`: Inverse accumulator resolution ratio (default: `1`)
- `--min_dist`: Minimum distance between circle centers (default: `270`)
- `--param1`: First Canny param (default: `45`)
- `--param2`: Accumulator threshold (default: `20`)
- `--min_radius`: Minimum circle radius (default: `120`)
- `--max_radius`: Maximum circle radius (default: `145`)

If a config file is provided, values are defaulted as list above.

#### config — Generate Config File

Create a new default configuration TOML file which can be used while processing images.

`lemna config -f config.toml`