# pydouble-slit

A small Python package to simulate the double slit experiment using quantum wavefunctions.

## Features

- Simulate electron detection patterns with and without slit measurement
- Visualize 2D detection histograms and 1D detection distributions
- Easily configurable slit distance, screen distance, and screen size

## Installation

You can install this package using pip (after building and uploading to PyPI):


## Usage

```python
from pydouble_slit import doubleSlit

# Create a double slit experiment instance
experiment = doubleSlit(slit_dist=1, distance_to_screen=10, screen_width=200, screen_height=100, measure_slit=False)

# Fire a single electron
experiment.fire_electron()

# Fire a beam of electrons
experiment.electron_beam(num_electrons=5000)

# Show the 2D detection screen
experiment.show_screen()

# Show the 1D histogram of detections
experiment.show_hist()

# Clear the screen for a new experiment
experiment.clear_screen()
```

## Requirements

- Python 3.9+
- numpy
- matplotlib
- scipy

## License

MIT License

## Author

Example Author  
[author@example.com](mailto:author@example.com)