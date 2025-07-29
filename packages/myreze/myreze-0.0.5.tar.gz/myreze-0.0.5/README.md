# Myreze

Myreze is a data passing, processing and visualization toolkit for handling geospatial data and rendering it through different visualization engines. It provides a unified interface for managing, validating, and visualizing geospatial data with time components.

## Installation

```bash
pip install -e .
```

## Core Concepts

Myreze is built around these core concepts:

- **Data Packages**: Container for geospatial data with time information
- **Time**: Flexible time representation (timestamps, spans, series)
- **Renderers**: Visualization schemas for different platforms
- **Visualization Types**: Metadata indicating how data should be interpreted and rendered

## Usage

### Creating a Data Package

```python
from myreze.data import MyrezeDataPackage, Time

# Create a timestamp for your data
time_data = Time.timestamp("2023-01-01T00:00:00Z")

# Create a data package with your geospatial data
data_package = MyrezeDataPackage(
    id="my-geodata",
    data={"points": [[lat1, lon1], [lat2, lon2]]},
    time=time_data,
    metadata={"creator": "Your Name", "description": "Sample dataset"},
    visualization_type="point_cloud"  # Indicates how to visualize the data
)

# Export to JSON
json_data = data_package.to_json()
```

### Visualization Types

The `visualization_type` field helps receivers understand how to interpret and visualize your data. This is crucial when your data package is processed by different visualization engines.

#### Common Visualization Types

- `"flat_overlay"` - 2D overlays like weather maps, satellite imagery
- `"point_cloud"` - Scattered data points (weather stations, sensors)
- `"heatmap"` - Continuous data surfaces (temperature, pressure)
- `"vector_field"` - Directional data (wind, ocean currents)
- `"terrain"` - 3D elevation data
- `"trajectory"` - Path or route data over time
- `"contour"` - Isoline representations (pressure contours, elevation contours)

#### Example: Weather Overlay

```python
from myreze.data import MyrezeDataPackage, Time
import numpy as np

# Temperature data as a 2D grid
temperature_data = {
    "grid": np.random.rand(100, 100),  # Temperature values
    "bounds": [-10, 50, 10, 60],       # Geographic bounds [west, south, east, north]
    "units": "celsius"
}

data_package = MyrezeDataPackage(
    id="temperature-overlay",
    data=temperature_data,
    time=Time.timestamp("2023-01-01T12:00:00Z"),
    visualization_type="flat_overlay",
    metadata={
        "description": "Temperature overlay for weather visualization",
        "colormap": "viridis",
        "min_value": -20,
        "max_value": 40
    }
)
```

### Visualizing with Three.js

```python
from myreze.data import MyrezeDataPackage
from myreze.viz import ThreeJSRenderer

# Create a data package with visualization type
data_package = MyrezeDataPackage(
    id="visualization-example",
    data=your_data,
    time=your_time,
    threejs_visualization=ThreeJSRenderer(),
    visualization_type="heatmap"  # Tells the receiver how to interpret the data
)

# Generate visualization
visualization = data_package.to_threejs(params={})
```

### Visualizing with Unreal Engine

```python
from myreze.data import MyrezeDataPackage
from myreze.viz import UnrealRenderer

# Create a data package with visualization type
data_package = MyrezeDataPackage(
    id="unreal-example",
    data=your_data,
    time=your_time,
    unreal_visualization=UnrealRenderer(),
    visualization_type="terrain"  # Indicates 3D terrain rendering
)

# Generate visualization
visualization = data_package.to_unreal(params={})
```

## Time Handling

Myreze provides flexible time handling:

```python
from myreze.data import Time

# Single timestamp
timestamp = Time.timestamp("2023-01-01T00:00:00Z")

# Time span
timespan = Time.span("2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z")

# Time series
timeseries = Time.series([
    "2023-01-01T00:00:00Z",
    "2023-01-01T01:00:00Z",
    "2023-01-01T02:00:00Z"
])
```

## Package Components

- **data**: Core data structures and validation
- **viz**: Visualization renderers for various platforms
  - **threejs**: Web-based 3D visualizations
  - **unreal**: Unreal Engine visualizations
  - **png**: Static image export

## Development

### Update PyPI 

```shell
python -m build
python -m twine upload dist/*
```

## Dependencies

- numpy: For numerical operations
- isodate: For ISO 8601 parsing

## Data conventions

For convenience, let's stick to some simple rules:

- Use Web Mercator WGS84 auxiliary sphere (EPSG 3857) when passing geolocations (like bounding boxes). See 
-  Return geolocated data normalized to the (0,1) planar region.
-  Let the second component (y) in the returned geometries point up.
-  Place any layers at y=0 offset.

## Documentation

See the [API documentation](docs/api.md) and [tutorial](docs/tutorial.md) for more information.
