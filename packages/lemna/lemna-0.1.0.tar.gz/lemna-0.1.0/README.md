# Lemna
A simple app utilizing computer vision (openCV) which identifies wells and calculates the area for any region that matches the given mask (HSV lower-upper).

## Getting Started

### Dependencies

* [Python 3](https://www.python.org/downloads/)
* [Click](https://click.palletsprojects.com/en/8.1.x/)
* [numpy](https://numpy.org/)
* [openCV](https://opencv.org/)

Following the install process below will add all dependecies (except for Python since it is required for installation and use).

### Installing

Clone or download a zip of the repository.

`git clone https://github.com/jonathanmsnow/frond-area-cv.git`

Navigate to the root directory of the cloned repository. You should see a file called `setup.py`.


Now you should [create and activate a virtual environment for Python](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/). 

Once you are in your virtualenv, install the app using pip.

`pip install --editable .`

### Commands

You can use the app by typing `analyzer` in the terminal. Typing `analyzer --help` will show available commands.
##### threshold
This allows you to open an image to determine the HSV upper and lower bound needed to isolate your points of interest in the image (e.g. fronds in wells).

- Usage
  `analyzer threshold -i <path_to_image> -w <width_to_display_image>`

##### process
This allows you to open an image or directory of images to be processed by identifying wells and measuring area in each of those wells.

- Usage
  `analyzer process -i <path_to_image>`
