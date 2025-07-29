"""
High-level simulation interface for WindNinjaPy.

This module provides the main WindSimulation class that serves as the
primary interface for running wind simulations.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

from .types import (
    BoundingBox,
    CloudCover,
    Coordinates,
    DiurnalWindsOption,
    Point,
    SimulationConfig,
    StabilityClass,
    VegetationType,
    WeatherStation,
    WindResult,
)

logger = logging.getLogger(__name__)


class WindSimulation:
    """
    High-level interface for WindNinja wind simulations.

    This class provides a Pythonic interface to the WindNinja C++ library,
    allowing users to configure and run wind simulations with minimal setup.

    Example:
        >>> simulation = WindSimulation()
        >>> simulation.set_dem("elevation.tif")
        >>> simulation.set_uniform_wind(speed=10.0, direction=270.0)
        >>> result = simulation.run()
        >>> print(f"Max wind speed: {result.wind_speed.max():.2f} m/s")
    """

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        """
        Initialize a new wind simulation.

        Args:
            config: Optional simulation configuration. If None, creates default config.
        """
        self._config = config or SimulationConfig(dem_file="")
        self._weather_stations: List[WeatherStation] = []
        self._is_configured = False

        # Cache for simulation results to avoid memory management issues
        self._cached_result: Optional[WindResult] = None
        self._last_config_hash: Optional[str] = None

        # Will be set when C++ bindings are available
        self._cpp_simulation = None

    @property
    def config(self) -> SimulationConfig:
        """Get the current simulation configuration."""
        return self._config

    def _clear_cache(self) -> None:
        """Clear the cached simulation results."""
        self._cached_result = None
        self._last_config_hash = None

    def set_dem(self, dem_file: Union[str, Path]) -> None:
        """
        Set the Digital Elevation Model (DEM) file.

        Args:
            dem_file: Path to the DEM file (GeoTIFF format recommended)

        Raises:
            FileNotFoundError: If the DEM file doesn't exist
            ValueError: If the file format is not supported
        """
        dem_path = Path(dem_file)
        if not dem_path.exists():
            raise FileNotFoundError(f"DEM file not found: {dem_file}")

        # Basic file extension validation
        valid_extensions = {".tif", ".tiff", ".asc", ".dem"}
        if dem_path.suffix.lower() not in valid_extensions:
            logger.warning(
                f"DEM file extension '{dem_path.suffix}' may not be supported. "
                f"Recommended formats: {', '.join(valid_extensions)}"
            )

        self._config.dem_file = str(dem_path.absolute())
        self._is_configured = True
        self._clear_cache()  # Clear cache when configuration changes

    def set_uniform_wind(
        self,
        speed: float,
        direction: float,
        vegetation_type: VegetationType = VegetationType.GRASS,
        stability_class: StabilityClass = StabilityClass.NEUTRAL,
    ) -> None:
        """
        Configure the simulation for uniform wind conditions.

        Args:
            speed: Wind speed in m/s
            direction: Wind direction in degrees (0=north, 90=east, etc.)
            vegetation_type: Type of vegetation for surface roughness
            stability_class: Atmospheric stability class

        Raises:
            ValueError: If wind parameters are invalid
        """
        if speed < 0:
            raise ValueError("Wind speed must be non-negative")
        if not (0 <= direction < 360):
            raise ValueError("Wind direction must be between 0 and 360 degrees")

        self._config.input_wind_speed = speed
        self._config.input_wind_direction = direction
        self._config.vegetation_type = vegetation_type
        self._config.stability_class = stability_class

        # Clear existing weather stations as they're incompatible with uniform wind
        if self._weather_stations:
            logger.info("Clearing weather stations (incompatible with uniform wind)")
            self._weather_stations.clear()

        self._is_configured = True
        self._clear_cache()  # Clear cache when configuration changes

        logger.info(
            f"Set uniform wind: {speed} m/s from {direction}° "
            f"(vegetation: {vegetation_type.value}, stability: {stability_class.value})"
        )

    def add_weather_station(
        self,
        location: Coordinates,
        wind_speed: float,
        wind_direction: float,
        temperature: Optional[float] = None,
        relative_humidity: Optional[float] = None,
    ) -> None:
        """
        Add a weather station for point initialization mode.

        Args:
            location: Station location as Point or (x, y) tuple
            wind_speed: Wind speed at the station in m/s
            wind_direction: Wind direction at the station in degrees
            temperature: Optional temperature in Celsius
            relative_humidity: Optional relative humidity in percent
        """
        if isinstance(location, tuple):
            location = Point(x=location[0], y=location[1])

        station = WeatherStation(
            location=location,
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            temperature=temperature,
            relative_humidity=relative_humidity,
        )

        # Clear uniform wind settings since we're using point initialization
        if self._config.input_wind_speed is not None:
            logger.info("Clearing uniform wind (incompatible with weather stations)")
            self._config.input_wind_speed = None
            self._config.input_wind_direction = None

        self._weather_stations.append(station)
        self._is_configured = True
        self._clear_cache()  # Clear cache when configuration changes

        logger.info(
            f"Added weather station at {location} "
            f"({wind_speed} m/s from {wind_direction}°)"
        )

    def set_diurnal_winds(
        self,
        enabled: bool = True,
        simulation_time: Optional[str] = None,
        time_zone: Optional[str] = None,
        cloud_cover: CloudCover = CloudCover.CLEAR,
    ) -> None:
        """
        Configure diurnal slope wind modeling.

        Args:
            enabled: Whether to enable diurnal wind effects
            simulation_time: Time in ISO format "YYYY-MM-DDTHH:MM:SS"
            time_zone: Time zone string (e.g., "America/Denver")
            cloud_cover: Cloud cover conditions
        """
        self._config.diurnal_winds = (
            DiurnalWindsOption.ENABLED if enabled else DiurnalWindsOption.DISABLED
        )
        self._config.simulation_time = simulation_time
        self._config.time_zone = time_zone
        self._config.cloud_cover = cloud_cover

        self._clear_cache()  # Clear cache when configuration changes

        logger.info(
            f"Set diurnal winds: {enabled} "
            f"(time: {simulation_time}, zone: {time_zone})"
        )

    def set_mesh_resolution(self, resolution: float) -> None:
        """
        Set the computational mesh resolution.

        Args:
            resolution: Grid resolution in meters

        Raises:
            ValueError: If resolution is not positive
        """
        if resolution <= 0:
            raise ValueError("Mesh resolution must be positive")

        self._config.mesh_resolution = resolution
        self._clear_cache()  # Clear cache when configuration changes
        logger.info(f"Set mesh resolution: {resolution} m")

    def set_output_height(self, height: float) -> None:
        """
        Set the height above ground for wind output.

        Args:
            height: Height in meters above ground level

        Raises:
            ValueError: If height is not positive
        """
        if height <= 0:
            raise ValueError("Output height must be positive")

        self._config.output_wind_height = height
        self._clear_cache()  # Clear cache when configuration changes
        logger.info(f"Set output height: {height} m above ground")

    def set_num_threads(self, num_threads: int) -> None:
        """
        Set the number of threads for parallel computation.

        Args:
            num_threads: Number of threads to use

        Raises:
            ValueError: If num_threads is less than 1
        """
        if num_threads < 1:
            raise ValueError("Number of threads must be at least 1")

        self._config.num_threads = num_threads
        logger.info(f"Set number of threads: {num_threads}")

    def validate_configuration(self) -> None:
        """
        Validate the current simulation configuration.

        Raises:
            ValueError: If the configuration is invalid or incomplete
        """
        if not self._config.dem_file:
            raise ValueError("DEM file must be specified")

        if not Path(self._config.dem_file).exists():
            raise ValueError(f"DEM file not found: {self._config.dem_file}")

        # Check that we have either uniform wind or weather stations
        has_uniform_wind = (
            self._config.input_wind_speed is not None
            and self._config.input_wind_direction is not None
        )
        has_weather_stations = len(self._weather_stations) > 0

        if not (has_uniform_wind or has_weather_stations):
            raise ValueError(
                "Must specify either uniform wind conditions or weather stations"
            )

        if has_uniform_wind and has_weather_stations:
            raise ValueError("Cannot specify both uniform wind and weather stations")

        # Validate diurnal settings
        if self._config.diurnal_winds == DiurnalWindsOption.ENABLED:
            if not self._config.simulation_time:
                raise ValueError(
                    "simulation_time required when diurnal winds are enabled"
                )

    def _compute_config_hash(self) -> str:
        """Compute a hash of the current configuration for caching."""
        import hashlib

        # Create a string representation of all configuration that affects results
        config_str = (
            f"{self._config.dem_file}|{self._config.input_wind_speed}|"
            f"{self._config.input_wind_direction}|"
        )
        config_str += (
            f"{self._config.vegetation_type}|{self._config.output_wind_height}|"
            f"{self._config.num_vertical_layers}|"
        )
        config_str += (
            f"{self._config.mesh_resolution}|{self._config.diurnal_winds}|"
            f"{self._config.simulation_time}|"
        )
        config_str += f"{self._config.time_zone}|{len(self._weather_stations)}|"

        # Add weather station data to hash
        for station in self._weather_stations:
            config_str += (
                f"{station.location}|{station.wind_speed}|{station.wind_direction}|"
            )

        return hashlib.md5(config_str.encode()).hexdigest()

    def run(self) -> WindResult:
        """
        Run the wind simulation.

        Returns:
            WindResult containing the simulation outputs

        Raises:
            ValueError: If the configuration is invalid
            RuntimeError: If the simulation fails
        """
        # Validate configuration before running
        self.validate_configuration()

        # Check if we can return cached results
        current_config_hash = self._compute_config_hash()
        if (
            self._cached_result is not None
            and self._last_config_hash == current_config_hash
        ):
            logger.info("Returning cached simulation results")
            return self._cached_result

        logger.info("Starting wind simulation...")

        # Import the working C API bindings
        try:
            from . import WindNinjaCore, is_windninja_available

            if not is_windninja_available():
                raise RuntimeError(
                    "WindNinja C API library not available. "
                    "Please check your installation."
                )
        except ImportError:
            raise RuntimeError(
                "WindNinja Python bindings not available. "
                "Please ensure the C++ extension was built successfully."
            )

        # Create the C API simulation instance
        try:
            cpp_sim = WindNinjaCore()

            # Configure the C++ simulation
            logger.info(f"Setting DEM file: {self._config.dem_file}")
            cpp_sim.set_dem_file(self._config.dem_file)

            # Set uniform wind if specified
            if (
                self._config.input_wind_speed is not None
                and self._config.input_wind_direction is not None
            ):
                logger.info(
                    f"Setting uniform wind: {self._config.input_wind_speed} m/s "
                    f"from {self._config.input_wind_direction}°"
                )
                cpp_sim.set_uniform_wind(
                    speed=self._config.input_wind_speed,
                    direction=self._config.input_wind_direction,
                    speed_units="mps",
                )
                # Note: Domain average initialization handled automatically in C API

            # Set vegetation type
            if self._config.vegetation_type:
                vegetation_map = {
                    VegetationType.GRASS: "grass",
                    VegetationType.BRUSH: "brush",
                    VegetationType.TREES: "trees",
                }
                veg_str = vegetation_map.get(self._config.vegetation_type, "grass")
                logger.info(f"Setting vegetation: {veg_str}")
                cpp_sim.set_vegetation(veg_str)

            # Set mesh choice for performance
            cpp_sim.set_mesh_choice("coarse")

            # Set output height
            if self._config.output_wind_height:
                logger.info(
                    f"Setting output height: {self._config.output_wind_height} m"
                )
                cpp_sim.set_wind_height(self._config.output_wind_height, "m")

            # Set number of layers instead of mesh resolution
            if self._config.num_vertical_layers:
                logger.info(
                    f"Setting number of layers: {self._config.num_vertical_layers}"
                )
                cpp_sim.set_num_layers(self._config.num_vertical_layers)

            # Set diurnal winds if enabled
            if self._config.diurnal_winds == DiurnalWindsOption.ENABLED:
                logger.info("Enabling diurnal winds")
                cpp_sim.set_diurnal_winds(True)

                # Set date/time if specified
                if self._config.simulation_time:
                    # Parse ISO format datetime: "2024-02-02T02:00:00"
                    import datetime

                    try:
                        dt = datetime.datetime.fromisoformat(
                            self._config.simulation_time.replace("Z", "+00:00")
                        )
                        timezone = self._config.time_zone or "UTC"

                        logger.info(
                            f"Setting date/time: {dt.year}-{dt.month:02d}-"
                            f"{dt.day:02d} {dt.hour:02d}:{dt.minute:02d} {timezone}"
                        )
                        cpp_sim.set_date_time(
                            dt.year, dt.month, dt.day, dt.hour, dt.minute, timezone
                        )

                        # Set default air temperature (15°C) for diurnal calculations
                        logger.info("Setting air temperature: 15.0°C for diurnal winds")
                        cpp_sim.set_air_temperature(15.0, "C")

                        # Set default cloud cover (50%) for diurnal calculations
                        logger.info(
                            "Setting cloud cover: 0.5 (fraction) for diurnal winds"
                        )
                        cpp_sim.set_cloud_cover(0.5, "fraction")

                    except ValueError as e:
                        logger.warning(
                            f"Could not parse simulation_time "
                            f"'{self._config.simulation_time}': {e}"
                        )
                        logger.info(
                            "Using default date/time and weather for diurnal winds"
                        )
                        # Use defaults already set in C++ wrapper
                else:
                    logger.info("Using default date/time and weather for diurnal winds")
            else:
                cpp_sim.set_diurnal_winds(False)

            # Run the simulation
            logger.info("Running WindNinja simulation...")
            success = cpp_sim.simulate()

            if not success:
                raise RuntimeError("WindNinja simulation failed")

            logger.info("Simulation completed successfully")

            # Get results immediately after simulation (while C++ object is still valid)
            logger.info("Retrieving simulation results...")
            speed_grid = cpp_sim.get_output_speed_grid()
            direction_grid = cpp_sim.get_output_direction_grid()

            # Immediately copy the data to ensure we have our own memory-safe copies
            import numpy as np

            speed_grid = np.array(speed_grid, copy=True)  # Force a copy
            direction_grid = np.array(direction_grid, copy=True)  # Force a copy
            logger.info("Grid data copied to safe Python arrays")

            # Create WindResult object and cache it
            from .types import BoundingBox, WindResult

            # Create dummy bounds (would be extracted from DEM in real impl)
            dummy_bounds = BoundingBox(
                min_x=0.0,
                min_y=0.0,
                max_x=float(speed_grid.shape[1]),
                max_y=float(speed_grid.shape[0]),
            )

            result = WindResult(
                wind_speed=speed_grid,
                wind_direction=direction_grid,
                u_component=speed_grid * np.cos(np.radians(270 - direction_grid)),
                v_component=speed_grid * np.sin(np.radians(270 - direction_grid)),
                bounds=dummy_bounds,
                resolution=self._config.mesh_resolution
                or 100.0,  # Default resolution if not set
            )

            # Cache the result and configuration hash
            self._cached_result = result
            self._last_config_hash = current_config_hash

            logger.info(
                f"Results cached: {speed_grid.shape} grid, "
                f"max speed: {speed_grid.max():.2f} m/s"
            )
            return result

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            raise RuntimeError(f"WindNinja simulation failed: {e}") from e

    def get_domain_bounds(self) -> Optional[BoundingBox]:
        """
        Get the geographical bounds of the simulation domain.

        Returns:
            BoundingBox of the domain, or None if DEM not loaded
        """
        if not self._config.dem_file:
            return None

        # This would extract bounds from the DEM file
        # For now, return None since we need GDAL integration
        return None

    def estimate_runtime(self) -> Optional[float]:
        """
        Estimate the simulation runtime in seconds.

        Returns:
            Estimated runtime in seconds, or None if cannot estimate
        """
        # This would analyze the domain size, mesh resolution, etc.
        # to provide a runtime estimate
        return None

    def __repr__(self) -> str:
        """String representation of the simulation."""
        dem_file = (
            Path(self._config.dem_file).name if self._config.dem_file else "Not set"
        )
        wind_mode = (
            "Uniform wind" if self._config.input_wind_speed else "Weather stations"
        )

        return (
            f"WindSimulation(dem='{dem_file}', mode='{wind_mode}', "
            f"configured={self._is_configured})"
        )
