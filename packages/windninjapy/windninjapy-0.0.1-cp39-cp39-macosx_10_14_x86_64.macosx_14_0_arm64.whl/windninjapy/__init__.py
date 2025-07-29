"""
WindNinjaPy: Python bindings for the WindNinja wind simulation library.

This package provides a Pythonic interface to the WindNinja C++ library,
enabling high-resolution wind field simulations for wildland fire modeling
and other applications requiring terrain-aware wind prediction.
"""

import os
from typing import Optional

# Version information
__version__ = "0.1.0"
__author__ = "WindNinja Python Bindings Team"
__email__ = "windninja@example.com"

# Set up WindNinja data directory automatically
def _setup_windninja_data():
    """Automatically set WINDNINJA_DATA environment variable if not already set."""
    if "WINDNINJA_DATA" not in os.environ:
        # Find the data directory relative to this module
        package_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(package_dir, "data")
        
        if os.path.exists(data_dir):
            os.environ["WINDNINJA_DATA"] = data_dir
            print(f"✓ Set WINDNINJA_DATA to: {data_dir}")
        else:
            print(f"⚠️  Warning: WindNinja data directory not found at {data_dir}")
    else:
        print(f"✓ WINDNINJA_DATA already set to: {os.environ['WINDNINJA_DATA']}")

# Initialize WindNinja data path
_setup_windninja_data()

# Core imports
try:
    # Import the compiled C++ extension module
    from ._windninja_core import WindNinjaCore, get_version_info, is_available

    # Create an alias for easier use
    WindNinja = WindNinjaCore

    # Set up availability flags
    _WINDNINJA_AVAILABLE = is_available()
    _IMPORT_ERROR = None

    # Note: cleanup_all_armies function not available in current build
    # atexit.register(cleanup_all_armies)
except ImportError as e:
    # If the C++ extension is not available, set flags
    _WINDNINJA_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    WindNinja = None
    WindNinjaCore = None


def is_windninja_available() -> bool:
    """
    Check if the WindNinja C++ library is available.

    Returns:
        bool: True if WindNinja C++ bindings are loaded successfully, False otherwise.
    """
    return bool(_WINDNINJA_AVAILABLE)


def get_windninja_info() -> Optional[str]:
    """
    Get information about the WindNinja installation.

    Returns:
        Optional[str]: Version and build information if available, None otherwise.
    """
    if not _WINDNINJA_AVAILABLE:
        return f"WindNinja not available: {_IMPORT_ERROR}"

    try:
        version_info = get_version_info()
        return str(version_info) if version_info is not None else None
    except (ImportError, AttributeError):
        return "WindNinja core available, version information not accessible"


# Define what gets imported with "from windninjapy import *"
__all__ = [
    # Core classes
    "WindNinja",
    "WindNinjaCore",
    # Information functions
    "is_windninja_available",
    "get_windninja_info",
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
]
