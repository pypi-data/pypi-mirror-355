# ji
A toolbox for planar projections (2D embeddings) of high-dimensional data.

To install: `pip install ji`

## Overview
The `ji` package provides a suite of tools for embedding high-dimensional data into two dimensions using various techniques, including PCA, Isomap, LLE, t-SNE, and more. It is useful for visualization, data compression, and as a preprocessing step for machine learning.

## Main Features
- **Dimensionality Reduction**: Project high-dimensional data to 2D using a variety of methods.
- **Visualization**: Includes a function to create scatter plots of the embedded data.
- **Extensible**: Easily add more embedding methods or custom plotting functions.

## Usage Examples

### Demo: Listing and Using Planarizers
```python
from ji import planarizers
# List available planarizers
print(sorted(planarizers))
# Prepare some data
X = [[1,2,3,4],[4,3,2,1],[0,0,0,0],[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4]]
y = [0,1,2,0,1,2,0]
# Use a planarizer that only uses X
pts = planarizers['identity'](X)
print(pts)
# Use a planarizer that arranges points in a circle
pts2 = planarizers['circular'](X)
print(pts2)
```

### Using the `analyze` Function
The `analyze` function runs several planarizers and visualizes the results. It uses the `planarizers` registry, so you can easily add or use custom methods.

```python
from ji import analyze
# Assuming X and y are already defined
analyze(X, y)
```

If you do not specify `X` and `y`, `analyze` will load a pre-defined digits dataset and perform the analysis on it:

```python
from ji import analyze
analyze()
```

### Custom Plot Function
You can pass a custom plotting function to `analyze`:

```python
from ji import analyze
import matplotlib.pyplot as plt

def custom_plot(X, y):
    plt.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis', edgecolor='k')
    plt.show()

analyze(plot_fun=custom_plot)
```

### Testing
A test/demo function is provided:
```python
from ji import test_planarizers
test_planarizers()
```

## Documentation

### `scatter_plot(X, y)`
Plots a simple scatter plot of the data.
- **Parameters**:
  - `X`: 2D numpy array, the data points to plot.
  - `y`: 1D numpy array, the target labels for coloring the points.

### `analyze(X=None, y=None, plot_fun=scatter_plot, data_name='data', methods=None)`
Main function to perform and visualize various embeddings using the planarizers registry.
- **Parameters**:
  - `X`: 2D numpy array, the input data. If `None`, a default dataset (digits) is loaded.
  - `y`: 1D numpy array, the target labels corresponding to `X`. Required if `X` is not `None`.
  - `plot_fun`: Function used to plot the embedding. Defaults to `scatter_plot`.
  - `data_name`: String, a name for the dataset to be displayed in plot titles.
  - `methods`: List of planarizer names to use (defaults to a subset).

This package is designed to be a practical tool in both educational and research settings for those interested in machine learning, data science, and pattern recognition.