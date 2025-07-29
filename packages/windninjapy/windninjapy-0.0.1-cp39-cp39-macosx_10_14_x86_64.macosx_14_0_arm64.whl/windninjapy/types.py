"""
Type definitions and data structures for WindNinjaPy.

This module defines the core data types, enums, and dataclasses used
throughout the WindNinjaPy API.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt


class VegetationType(Enum):
    """Vegetation types supported by WindNinja simulations."""

    GRASS = "grass"
    BRUSH = "brush"
    TREES = "trees"

    def __str__(self) -> str:
        return self.value


class StabilityClass(Enum):
    """Atmospheric stability classes for WindNinja simulations."""

    EXTREMELY_UNSTABLE = "extremely_unstable"
    MODERATELY_UNSTABLE = "moderately_unstable"
    SLIGHTLY_UNSTABLE = "slightly_unstable"
    NEUTRAL = "neutral"
    SLIGHTLY_STABLE = "slightly_stable"
    MODERATELY_STABLE = "moderately_stable"
    EXTREMELY_STABLE = "extremely_stable"


class DiurnalWindsOption(Enum):
    """Options for diurnal slope wind modeling."""

    DISABLED = "disabled"
    ENABLED = "enabled"


class CloudCover(Enum):
    """Cloud cover options for diurnal calculations."""

    CLEAR = "clear"
    FEW = "few"
    SCATTERED = "scattered"
    BROKEN = "broken"
    OVERCAST = "overcast"


@dataclass
class Point:
    """A geographical point with coordinates."""

    x: float  # Longitude or easting
    y: float  # Latitude or northing

    def __post_init__(self) -> None:
        """Validate point coordinates."""
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise TypeError("Point coordinates must be numeric")


@dataclass
class BoundingBox:
    """A geographical bounding box defined by min/max coordinates."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        """Validate bounding box coordinates."""
        if self.min_x >= self.max_x:
            raise ValueError("min_x must be less than max_x")
        if self.min_y >= self.max_y:
            raise ValueError("min_y must be less than max_y")

    @property
    def width(self) -> float:
        """Get the width of the bounding box."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Get the height of the bounding box."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Point:
        """Get the center point of the bounding box."""
        return Point(x=(self.min_x + self.max_x) / 2, y=(self.min_y + self.max_y) / 2)


@dataclass
class SimulationConfig:
    """Configuration parameters for a WindNinja simulation."""

    # Required parameters
    dem_file: str
    output_wind_height: float = 10.0  # meters above ground

    # Wind input parameters
    input_wind_speed: Optional[float] = None  # m/s
    input_wind_direction: Optional[float] = None  # degrees

    # Environmental parameters
    vegetation_type: VegetationType = VegetationType.GRASS
    stability_class: StabilityClass = StabilityClass.NEUTRAL
    diurnal_winds: DiurnalWindsOption = DiurnalWindsOption.DISABLED
    cloud_cover: CloudCover = CloudCover.CLEAR

    # Simulation parameters
    num_threads: int = 1
    mesh_resolution: Optional[float] = None  # meters, auto-calculated if None
    momentum_flag: bool = False  # use momentum solver vs. mass conservation
    num_vertical_layers: int = 20  # number of vertical mesh layers

    # Optional time parameters (for diurnal calculations)
    simulation_time: Optional[str] = None  # ISO format: "YYYY-MM-DDTHH:MM:SS"
    time_zone: Optional[str] = None  # e.g., "America/Denver"

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.output_wind_height <= 0:
            raise ValueError("output_wind_height must be positive")

        if self.input_wind_speed is not None and self.input_wind_speed < 0:
            raise ValueError("input_wind_speed must be non-negative")

        if self.input_wind_direction is not None:
            if not (0 <= self.input_wind_direction < 360):
                raise ValueError(
                    "input_wind_direction must be between 0 and 360 degrees"
                )

        if self.num_threads < 1:
            raise ValueError("num_threads must be at least 1")

        if self.mesh_resolution is not None and self.mesh_resolution <= 0:
            raise ValueError("mesh_resolution must be positive")

        if self.num_vertical_layers < 1:
            raise ValueError("num_vertical_layers must be at least 1")


@dataclass
class WindResult:
    """Results from a WindNinja simulation."""

    # Wind field arrays
    wind_speed: npt.NDArray[np.float64]  # 2D array of wind speeds (m/s)
    wind_direction: npt.NDArray[np.float64]  # 2D array of wind directions (degrees)

    # Wind vector components
    u_component: npt.NDArray[np.float64]  # East-west wind component (m/s)
    v_component: npt.NDArray[np.float64]  # North-south wind component (m/s)

    # Geospatial information
    bounds: BoundingBox  # Geographical bounds of the simulation domain
    resolution: float  # Grid resolution in meters

    # Optional elevation data
    elevation: Optional[npt.NDArray[np.float64]] = None  # 2D array of elevations (m)

    def __post_init__(self) -> None:
        """Validate result arrays have consistent shapes."""
        arrays = [
            self.wind_speed,
            self.wind_direction,
            self.u_component,
            self.v_component,
        ]

        if self.elevation is not None:
            arrays.append(self.elevation)

        shapes = [arr.shape for arr in arrays]
        if not all(shape == shapes[0] for shape in shapes):
            raise ValueError("All result arrays must have the same shape")

        if len(shapes[0]) != 2:
            raise ValueError("Result arrays must be 2-dimensional")

    @property
    def shape(self) -> Tuple[int, int]:
        """Get the shape of the result grids."""
        shape = self.wind_speed.shape
        return (shape[0], shape[1])

    @property
    def grid_points(self) -> int:
        """Get the total number of grid points."""
        return int(self.wind_speed.size)

    def get_wind_at_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Get wind speed and direction at a specific geographical point.

        Args:
            x: Longitude or easting coordinate
            y: Latitude or northing coordinate

        Returns:
            Tuple of (wind_speed, wind_direction) at the specified point

        Raises:
            ValueError: If the point is outside the simulation domain
        """
        if not (
            self.bounds.min_x <= x <= self.bounds.max_x
            and self.bounds.min_y <= y <= self.bounds.max_y
        ):
            raise ValueError("Point is outside simulation domain")

        # Convert geographical coordinates to array indices
        i = int((y - self.bounds.min_y) / self.resolution)
        j = int((x - self.bounds.min_x) / self.resolution)

        # Clamp to valid indices
        i = max(0, min(i, self.shape[0] - 1))
        j = max(0, min(j, self.shape[1] - 1))

        return float(self.wind_speed[i, j]), float(self.wind_direction[i, j])


@dataclass
class WeatherStation:
    """Weather station data for point initialization mode."""

    location: Point
    wind_speed: float  # m/s
    wind_direction: float  # degrees
    temperature: Optional[float] = None  # Celsius
    relative_humidity: Optional[float] = None  # percent

    def __post_init__(self) -> None:
        """Validate weather station data."""
        if self.wind_speed < 0:
            raise ValueError("wind_speed must be non-negative")

        if not (0 <= self.wind_direction < 360):
            raise ValueError("wind_direction must be between 0 and 360 degrees")

        if self.relative_humidity is not None:
            if not (0 <= self.relative_humidity <= 100):
                raise ValueError("relative_humidity must be between 0 and 100 percent")


# Type aliases for convenience
WindSpeedArray = npt.NDArray[np.float64]
WindDirectionArray = npt.NDArray[np.float64]
ElevationArray = npt.NDArray[np.float64]
Coordinates = Union[Point, Tuple[float, float]]
WeatherStations = List[WeatherStation]
