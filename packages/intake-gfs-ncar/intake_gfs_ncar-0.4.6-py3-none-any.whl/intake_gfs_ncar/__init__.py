"""Intake driver for NCAR GFS forecast data.

This package provides an Intake driver for accessing Global Forecast System (GFS)
data from the NCAR THREDDS server.
"""

import intake

from .gfs_intake_driver import GFSForecastSource

__version__ = "0.1.0"
__all__ = ["GFSForecastSource"]

# Register the driver if not already registered
try:
    intake.register_driver("gfs_forecast", GFSForecastSource, clobber=True)
except Exception:
    # If registration fails, the driver might already be registered
    # or there might be another issue, but we don't want to fail the import
    pass
