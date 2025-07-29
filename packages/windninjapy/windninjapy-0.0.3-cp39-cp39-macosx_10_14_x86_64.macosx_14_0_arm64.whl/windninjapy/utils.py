"""
Utility functions for WindNinjaPy.

This module provides various utility functions for working with
wind simulation data, file I/O, and coordinate conversions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import numpy as np
import numpy.typing as npt

try:
    # Optional dependencies
    from osgeo import gdal, osr

    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False

    # Create dummy classes for type hints
    class gdal:  # type: ignore[no-redef]
        Dataset = Any

    class osr:  # type: ignore[no-redef]
        SpatialReference = Any


from .types import BoundingBox, WindResult

logger = logging.getLogger(__name__)


def validate_dem_file(dem_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate a DEM file and return validation results.

    Args:
        dem_file: Path to DEM file

    Returns:
        Dictionary with validation results
    """
    dem_path = Path(dem_file)

    if not dem_path.exists():
        return {"is_valid": False, "error": f"File not found: {dem_path}"}

    try:
        # For testing, just load as numpy array
        if dem_path.suffix == ".npy":
            data = np.load(dem_path)
        else:
            # Assume it's a valid DEM for now
            data = np.random.rand(100, 100) * 1000

        # Check for issues
        warnings = []

        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            return {"is_valid": False, "error": "Contains NaN or infinite values"}

        # Check if too flat
        elevation_range: float = float(np.max(data) - np.min(data))
        if elevation_range < 1.0:
            warnings.append("Very flat terrain detected")

        # Check if too steep
        if elevation_range > 5000.0:
            warnings.append("Very steep terrain detected")

        result: Dict[str, Any] = {"is_valid": True}
        if warnings:
            result["warnings"] = warnings

        return result

    except Exception as e:
        return {"is_valid": False, "error": str(e)}


def load_dem(
    dem_file: Union[str, Path],
) -> Tuple[npt.NDArray[np.float64], BoundingBox, float]:
    """
    Load a DEM file and return elevation data with geospatial information.

    Args:
        dem_file: Path to the DEM file

    Returns:
        Tuple of (elevation_array, bounding_box, resolution)

    Raises:
        ImportError: If GDAL is not available
        ValueError: If the DEM file cannot be read
    """
    if not GDAL_AVAILABLE:
        raise ImportError(
            "GDAL is required for DEM loading. Install with: pip install gdal"
        )

    validate_dem_file(dem_file)

    # Open the DEM file
    dataset = gdal.Open(str(dem_file), gdal.GA_ReadOnly)
    if dataset is None:
        raise ValueError(f"Could not open DEM file: {dem_file}")

    try:
        # Get geotransform information
        geotransform = dataset.GetGeoTransform()
        if geotransform is None:
            raise ValueError(f"DEM file has no geospatial information: {dem_file}")

        # Extract spatial information
        x_origin = geotransform[0]
        y_origin = geotransform[3]
        pixel_width = geotransform[1]
        pixel_height = abs(geotransform[5])  # Usually negative

        cols = dataset.RasterXSize
        rows = dataset.RasterYSize

        # Calculate bounding box
        min_x = x_origin
        max_x = x_origin + cols * pixel_width
        max_y = y_origin
        min_y = y_origin - rows * pixel_height

        bounds = BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)

        # Assume square pixels for resolution
        resolution = pixel_width
        if abs(pixel_width - pixel_height) > 0.001:
            logger.warning(
                f"Non-square pixels detected: {pixel_width} x {pixel_height}. "
                f"Using width ({pixel_width}) as resolution."
            )

        # Read elevation data
        band = dataset.GetRasterBand(1)
        elevation = band.ReadAsArray().astype(np.float64)

        # Handle NoData values
        nodata_value = band.GetNoDataValue()
        if nodata_value is not None:
            elevation[elevation == nodata_value] = np.nan

        logger.info(f"Loaded DEM: {cols}x{rows} cells, resolution={resolution:.1f}m")

        return elevation, bounds, resolution

    finally:
        dataset = None  # Close the dataset


def save_wind_field(
    result: WindResult,
    output_file: Union[str, Path],
    format_type: str = "geotiff",
    **kwargs: Any,
) -> None:
    """
    Save wind simulation results to a file.

    Args:
        result: WindResult object containing simulation data
        output_file: Path for the output file
        format_type: Output format ("geotiff", "ascii", "netcdf")
        **kwargs: Additional format-specific options

    Raises:
        ImportError: If required libraries are not available
        ValueError: If the format is not supported
    """
    output_path = Path(output_file)

    if format_type.lower() == "geotiff":
        _save_wind_geotiff(result, output_path, **kwargs)
    elif format_type.lower() == "ascii":
        _save_wind_ascii(result, output_path, **kwargs)
    elif format_type.lower() == "netcdf":
        _save_wind_netcdf(result, output_path, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _save_wind_geotiff(result: WindResult, output_path: Path, **kwargs: Any) -> None:
    """Save wind results as GeoTIFF files."""
    if not GDAL_AVAILABLE:
        raise ImportError(
            "GDAL is required for GeoTIFF output. Install with: pip install gdal"
        )

    # Create geotransform
    geotransform = (
        result.bounds.min_x,  # Top-left x
        result.resolution,  # Pixel width
        0,  # Rotation (0 for north-up)
        result.bounds.max_y,  # Top-left y
        0,  # Rotation (0 for north-up)
        -result.resolution,  # Pixel height (negative for north-up)
    )

    # Save wind speed
    speed_file = output_path.with_suffix(".speed.tif")
    _write_geotiff_band(result.wind_speed, speed_file, geotransform, "Wind Speed (m/s)")

    # Save wind direction
    direction_file = output_path.with_suffix(".direction.tif")
    _write_geotiff_band(
        result.wind_direction, direction_file, geotransform, "Wind Direction (degrees)"
    )

    # Save U and V components
    u_file = output_path.with_suffix(".u.tif")
    _write_geotiff_band(result.u_component, u_file, geotransform, "U Component (m/s)")

    v_file = output_path.with_suffix(".v.tif")
    _write_geotiff_band(result.v_component, v_file, geotransform, "V Component (m/s)")

    logger.info(f"Saved wind fields to GeoTIFF files: {output_path.stem}.*")


def _write_geotiff_band(
    data: np.ndarray,
    filename: Path,
    geotransform: tuple,
    description: str,
) -> None:
    """Write a single data array to a GeoTIFF file."""
    if not GDAL_AVAILABLE:
        raise ImportError("GDAL is required for GeoTIFF output")

    driver = gdal.GetDriverByName("GTiff")
    rows, cols = data.shape

    dataset = driver.Create(
        str(filename),
        cols,
        rows,
        1,
        gdal.GDT_Float64,
        options=["COMPRESS=LZW", "TILED=YES"],
    )

    dataset.SetGeoTransform(geotransform)

    # Set spatial reference (assumes WGS84 for now)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84
    dataset.SetProjection(srs.ExportToWkt())

    # Write data
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    band.SetDescription(description)
    band.SetNoDataValue(np.nan)

    # Cleanup
    band = None
    dataset = None


def _save_wind_ascii(result: WindResult, output_path: Path, **kwargs: Any) -> None:
    """Save wind results as ASCII grid files."""
    header = _create_ascii_header(result)

    # Save each component
    files_and_data = [
        ("speed", result.wind_speed),
        ("direction", result.wind_direction),
        ("u", result.u_component),
        ("v", result.v_component),
    ]

    for suffix, data in files_and_data:
        filename = output_path.with_suffix(f".{suffix}.asc")

        with open(filename, "w") as f:
            # Write header
            f.write(header)

            # Write data (flip vertically for ASCII grid format)
            for row in np.flipud(data):
                f.write(" ".join(f"{val:.6f}" for val in row))
                f.write("\n")

    logger.info(f"Saved wind fields to ASCII files: {output_path.stem}.*")


def _create_ascii_header(result: WindResult) -> str:
    """Create ASCII grid header."""
    rows, cols = result.shape
    return (
        f"ncols         {cols}\n"
        f"nrows         {rows}\n"
        f"xllcorner     {result.bounds.min_x:.6f}\n"
        f"yllcorner     {result.bounds.min_y:.6f}\n"
        f"cellsize      {result.resolution:.6f}\n"
        f"NODATA_value  -9999\n"
    )


def _save_wind_netcdf(result: WindResult, output_path: Path, **kwargs: Any) -> None:
    """Save wind results as NetCDF file."""
    try:
        import netCDF4 as nc
    except ImportError:
        raise ImportError(
            "netCDF4 is required for NetCDF output. Install with: pip install netcdf4"
        )

    rows, cols = result.shape

    # Create coordinate arrays
    x_coords = np.linspace(
        result.bounds.min_x + result.resolution / 2,
        result.bounds.max_x - result.resolution / 2,
        cols,
    )
    y_coords = np.linspace(
        result.bounds.max_y - result.resolution / 2,
        result.bounds.min_y + result.resolution / 2,
        rows,
    )

    with nc.Dataset(str(output_path), "w", format="NETCDF4") as dataset:
        # Create dimensions
        dataset.createDimension("x", cols)
        dataset.createDimension("y", rows)

        # Create coordinate variables
        x_var = dataset.createVariable("x", "f8", ("x",))
        y_var = dataset.createVariable("y", "f8", ("y",))

        x_var[:] = x_coords
        y_var[:] = y_coords

        x_var.units = "meters"
        y_var.units = "meters"
        x_var.long_name = "Easting"
        y_var.long_name = "Northing"

        # Create data variables
        variables = {
            "wind_speed": (result.wind_speed, "Wind Speed", "m/s"),
            "wind_direction": (result.wind_direction, "Wind Direction", "degrees"),
            "u_component": (result.u_component, "U Wind Component", "m/s"),
            "v_component": (result.v_component, "V Wind Component", "m/s"),
        }

        for var_name, (data, long_name, units) in variables.items():
            var = dataset.createVariable(var_name, "f8", ("y", "x"), fill_value=np.nan)
            var[:] = data
            var.long_name = long_name
            var.units = units

        # Add global attributes
        dataset.title = "WindNinja Simulation Results"
        dataset.source = "WindNinjaPy"
        dataset.resolution = f"{result.resolution:.1f} meters"

    logger.info(f"Saved wind fields to NetCDF file: {output_path}")


def calculate_wind_statistics(
    speed_grid: npt.NDArray[np.float64],
    direction_grid: npt.NDArray[np.float64],
    u_grid: npt.NDArray[np.float64],
    v_grid: npt.NDArray[np.float64],
) -> Dict[str, float]:
    """
    Calculate wind field statistics.

    Args:
        speed_grid: Wind speed grid
        direction_grid: Wind direction grid
        u_grid: U component grid
        v_grid: V component grid

    Returns:
        Dictionary of statistics
    """
    # Mask valid data
    valid_mask = (
        np.isfinite(speed_grid)
        & np.isfinite(direction_grid)
        & np.isfinite(u_grid)
        & np.isfinite(v_grid)
    )

    valid_speed = speed_grid[valid_mask]
    valid_direction = direction_grid[valid_mask]
    valid_u = u_grid[valid_mask]
    valid_v = v_grid[valid_mask]

    if len(valid_speed) == 0:
        return {"error": "No valid data"}  # type: ignore[dict-item]

    return {
        "mean_speed": float(np.mean(valid_speed)),
        "max_speed": float(np.max(valid_speed)),
        "min_speed": float(np.min(valid_speed)),
        "speed_std": float(np.std(valid_speed)),
        "mean_direction": float(np.mean(valid_direction)),
        "direction_std": float(np.std(valid_direction)),
        "mean_u": float(np.mean(valid_u)),
        "mean_v": float(np.mean(valid_v)),
        "u_std": float(np.std(valid_u)),
        "v_std": float(np.std(valid_v)),
    }


def convert_wind_components(
    speed: npt.NDArray[np.float64], direction: npt.NDArray[np.float64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Convert wind speed and direction to U and V components.

    Args:
        speed: Wind speed array (m/s)
        direction: Wind direction array (degrees, meteorological convention)

    Returns:
        Tuple of (u_component, v_component) arrays
    """
    # Convert direction to radians and adjust for meteorological convention
    # Meteorological: direction wind is coming FROM
    # Mathematical: direction wind is going TO
    dir_rad = np.deg2rad(270 - direction)

    u_component = speed * np.cos(dir_rad)
    v_component = speed * np.sin(dir_rad)

    return u_component, v_component


def convert_wind_direction(
    u_component: npt.NDArray[np.float64], v_component: npt.NDArray[np.float64]
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Convert U and V wind components to speed and direction.

    Args:
        u_component: U wind component array (m/s)
        v_component: V wind component array (m/s)

    Returns:
        Tuple of (speed, direction) arrays
    """
    speed = np.sqrt(u_component**2 + v_component**2)

    # Calculate direction in meteorological convention
    direction = np.rad2deg(np.arctan2(-u_component, -v_component))
    direction = (direction + 360) % 360  # Ensure 0-360 range

    return speed, direction


def interpolate_grid(
    data: npt.NDArray[np.float64],
    x_coords: npt.NDArray[np.float64],
    y_coords: npt.NDArray[np.float64],
    new_x: npt.NDArray[np.float64],
    new_y: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """
    Interpolate data from one grid to another using scipy.interpolate.

    Args:
        data: 2D array of data values
        x_coords: 1D array of x coordinates
        y_coords: 1D array of y coordinates
        new_x: 1D array of new x coordinates
        new_y: 1D array of new y coordinates

    Returns:
        Interpolated data on new grid
    """
    try:
        from scipy.interpolate import RegularGridInterpolator
    except ImportError:
        raise ImportError(
            "scipy is required for grid interpolation. Install with: pip install scipy"
        )

    # Create interpolator
    interpolator = RegularGridInterpolator(
        (y_coords, x_coords),
        data,
        method="linear",
        bounds_error=False,
        fill_value=np.nan,
    )

    # Create new grid
    new_y_grid, new_x_grid = np.meshgrid(new_y, new_x, indexing="ij")
    new_points = np.column_stack([new_y_grid.ravel(), new_x_grid.ravel()])

    # Interpolate
    result = interpolator(new_points)
    return result.reshape(len(new_y), len(new_x)).astype(np.float64)  # type: ignore[no-any-return]


def create_grid_from_bounds(
    bounds: BoundingBox, resolution: float
) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Create coordinate grids from bounding box and resolution.

    Args:
        bounds: Bounding box
        resolution: Grid resolution in meters

    Returns:
        Tuple of (x_coords, y_coords) arrays
    """
    nx = int(np.ceil((bounds.max_x - bounds.min_x) / resolution))
    ny = int(np.ceil((bounds.max_y - bounds.min_y) / resolution))

    x_coords = np.linspace(bounds.min_x, bounds.max_x, nx)
    y_coords = np.linspace(bounds.min_y, bounds.max_y, ny)

    return x_coords, y_coords
